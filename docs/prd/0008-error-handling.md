# PRD-0008: Improved Error Handling

**Version:** 1.0
**Date:** 2026-03-13
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Improve error handling across the Open CIS stack so that users see actionable, specific error messages instead of generic "Network Error" or "Request failed: 500" messages. The primary focus is on EHRBase FLAT format composition errors, which currently propagate as unhandled 500s, but the solution covers all API error paths.

---

## Problem Statement

**Current State:**
- When EHRBase rejects a FLAT composition (e.g., invalid paths, "Could not consume Parts", missing required fields), the error propagates as an unhandled Python exception, resulting in a generic HTTP 500
- The frontend `api.ts` client attempts to parse `error.detail` from the response, but 500 errors from FastAPI's default handler don't always include a useful `detail` field
- If the response body isn't valid JSON (e.g., network timeout, proxy error), the catch in `api.ts:28` falls back to `"Request failed: {status}"` which is meaningless to users
- Service layer methods (`observation_service`, `cave_service`) catch broad `Exception` and return `None`/`False`, discarding the actual error details
- Users see messages like "Failed to record vital signs" with no indication of what went wrong or how to fix it

**User Personas:**
1. **Clinicians** - Need clear feedback when data entry fails ("Systolic value is required" vs. "Network Error")
2. **Developers/Learners** - Need to understand what went wrong with their openEHR compositions to learn the FLAT format
3. **System Administrators** - Need to distinguish between EHRBase being down vs. a data validation problem

---

## Goals & Success Metrics

### Goals
- Surface EHRBase validation errors as structured, user-readable API responses
- Distinguish between categories of errors (validation, not found, service unavailable, unexpected)
- Preserve error details for debugging without leaking internals to the UI
- Show contextual error messages in the frontend that help users fix the problem

### Success Metrics
- Zero "Network Error" messages for non-network errors
- EHRBase FLAT format errors return 422 with a human-readable message
- EHRBase connectivity issues return 503 with a "service unavailable" message
- Frontend displays error messages that match the actual problem

---

## Detailed Design

### 1. Backend: Custom Exception Hierarchy

Create `api/src/errors.py` with domain exceptions:

```python
class OpenCISError(Exception):
    """Base exception for Open CIS."""
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class EHRBaseValidationError(OpenCISError):
    """EHRBase rejected the composition (FLAT format errors, missing fields, etc.)."""
    pass

class EHRBaseUnavailableError(OpenCISError):
    """EHRBase is not reachable or returned a non-application error."""
    pass

class PatientNotFoundError(OpenCISError):
    """Patient does not exist or has no EHR."""
    pass

class CompositionNotFoundError(OpenCISError):
    """Composition UID does not exist."""
    pass
```

### 2. Backend: EHRBase Client Error Translation

Update `api/src/ehrbase/client.py` to catch `EHRBaseError` and `httpx` exceptions and translate them into the domain exceptions above.

Key behavior for `create_composition()`:
- Catch `EHRBaseError` and inspect the message/status code
- If it's a 400/422 from EHRBase (validation): raise `EHRBaseValidationError` with the EHRBase error body parsed into a readable message
- If it's a connection error or 5xx: raise `EHRBaseUnavailableError`
- Extract the most useful part of EHRBase's error response. Common EHRBase error patterns to parse:
  - `"Could not consume Parts"` - usually a `|value` suffix on a DV_TEXT or DV_DATE_TIME path
  - `"Required field missing"` - a mandatory archetype field was omitted
  - `"Unknown path"` - a FLAT path doesn't match the template

Example translation:
```python
async def create_composition(self, ehr_id, template_id, composition, format="FLAT"):
    try:
        client = await self._ensure_connected()
        result = await client.create_composition(...)
        return {...}
    except EHRBaseError as e:
        msg = str(e)
        if "Could not consume" in msg or "validation" in msg.lower():
            raise EHRBaseValidationError(
                message=f"EHRBase rejected the composition: {msg}",
                details={"template_id": template_id, "format": format},
            ) from e
        raise EHRBaseUnavailableError(
            message=f"EHRBase error: {msg}"
        ) from e
    except httpx.ConnectError as e:
        raise EHRBaseUnavailableError(
            message="Cannot connect to EHRBase. Is it running?"
        ) from e
```

### 3. Backend: FastAPI Exception Handlers

Register global exception handlers in `api/src/main.py` so that routers don't need individual try/except blocks for every domain error:

```python
@app.exception_handler(EHRBaseValidationError)
async def ehrbase_validation_handler(request, exc):
    return JSONResponse(status_code=422, content={
        "error": "validation_error",
        "message": exc.message,
        "details": exc.details,
    })

@app.exception_handler(EHRBaseUnavailableError)
async def ehrbase_unavailable_handler(request, exc):
    return JSONResponse(status_code=503, content={
        "error": "service_unavailable",
        "message": exc.message,
    })

@app.exception_handler(PatientNotFoundError)
async def patient_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={
        "error": "not_found",
        "message": exc.message,
    })
```

### 4. Backend: Standardized Error Response Schema

All error responses follow this shape (`details` is optional and defaults to `undefined` when omitted):

```json
{
  "error": "validation_error | not_found | service_unavailable | internal_error",
  "message": "Human-readable message suitable for display in the UI",
  "details": {"stacktrace": {}}
}

The `error` field is a machine-readable error code the frontend can use for branching logic (e.g., showing a retry button for `service_unavailable` but not for `validation_error`).

### 5. Backend: Service Layer Changes

Stop swallowing exceptions with broad `except Exception`. Instead:

- **Write paths** (`record_vital_signs`, `create_cave_entry`): Let `EHRBaseValidationError` and `EHRBaseUnavailableError` propagate to the global handler. Only catch `ValueError` for business logic issues (patient not found).
- **Read paths** (`get_vital_signs_for_patient`): Prefer propagating `EHRBaseUnavailableError` to return 503. If graceful degradation is retained for UX reasons, require an explicit `partial_data: true`/`degraded: true` response signal so outages are not misread as "no records".
- **Delete paths**: Prefer raising domain exceptions and mapping via global handlers instead of returning `False`, so clients receive specific failure causes.

### 6. Frontend: Enhanced API Client

Update `web/src/lib/api.ts` to parse the structured error response:

```typescript
interface ApiError {
  error: 'validation_error' | 'not_found' | 'service_unavailable' | 'internal_error'
  message: string
  details?: Record<string, unknown>
}

class ApiRequestError extends Error {
  code: string
  status: number
  details?: Record<string, unknown>

  constructor(status: number, body: ApiError) {
    super(body.message)
    this.code = body.error
    this.status = status
    this.details = body.details
  }
}

// In the request function:
if (!response.ok) {
  const body = await response.json().catch(() => ({
    error: 'internal_error',
    message: `Request failed (HTTP ${response.status})`,
  }))
  throw new ApiRequestError(response.status, body)
}
```

### 7. Frontend: Context-Aware Error Display

Stores and components can use the error code to show appropriate UI:

- `validation_error` (422): Show the message inline in the form. No retry button. The message from EHRBase should tell the user what's wrong.
- `service_unavailable` (503): Show a banner with a retry button: "EHRBase is currently unavailable. Please try again."
- `not_found` (404): Show "Record not found" - may indicate stale data, offer to refresh.
- `internal_error` (500): Show "Something went wrong. Please try again or contact support."

No changes to individual component templates are required in Phase 1 - the existing `error.value = e.message` pattern in stores will automatically show the better messages since `ApiRequestError.message` now contains the server's human-readable message.

---

## Implementation Phases

### Phase 1: Backend Error Structure (Minimal Viable)
1. Create `api/src/errors.py` with the exception hierarchy
2. Update `api/src/ehrbase/client.py` to translate `EHRBaseError` into domain exceptions
3. Register global exception handlers in `api/src/main.py`
4. Update `record_vital_signs` and `create_cave_entry` service methods to stop swallowing errors on write paths

**Result:** EHRBase FLAT errors now return 422 with a readable message instead of 500.

### Phase 2: Frontend Error Parsing
1. Add `ApiRequestError` class to `web/src/lib/api.ts`
2. Update `api.ts` request function to parse structured error responses

**Result:** Frontend stores automatically show better messages with no component changes.

### Phase 3: Enhanced Frontend UX (Optional)
1. Add error code awareness to dialog components (retry button for 503, inline message for 422)
2. Add a toast/notification system for transient errors
3. Add expandable "technical details" section for developers/learners

---

## Scope Boundaries

**In Scope:**
- EHRBase composition errors (FLAT format validation, connectivity)
- API error response standardization
- Frontend error message improvements
- Existing CRUD operations (vitals, CAVE, patients, encounters)

**Out of Scope:**
- Retry/circuit-breaker logic for EHRBase connectivity
- Client-side form validation mirroring EHRBase template constraints
- Error monitoring/alerting infrastructure
- Internationalization of error messages

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| EHRBase error messages change between versions | Parsed messages become wrong | Use substring matching, not exact string equality; log raw errors |
| Global exception handlers mask bugs | Real errors hidden as "validation errors" | Only map known error patterns; let truly unexpected errors remain as 500 |
| Breaking change to frontend error contract | Existing error handling stops working | `ApiRequestError` extends `Error`, so `e.message` still works everywhere |

---

## Open Questions

1. Should the `details` field in error responses include the FLAT composition that was sent, to help developers debug? (Privacy concern vs. developer experience)
2. Should we add a `/api/health` endpoint that checks both Prisma and EHRBase connectivity, so the frontend can proactively warn users?
