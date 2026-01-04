# ADR-0003: Direct httpx Integration for openEHR API

## Status
Accepted

## Context

Open CIS needs to interact with EHRBase (an openEHR Clinical Data Repository) to create, retrieve, and query clinical compositions. We must decide how to implement this integration: use an existing SDK/library or build a custom client using a low-level HTTP library.

### Problem

Clinical applications need to:
1. Create and manage EHRs (Electronic Health Records)
2. Store clinical data as compositions using templates
3. Query clinical data using AQL (Archetype Query Language)
4. Retrieve compositions in different formats (FLAT, STRUCTURED, CANONICAL)
5. Manage templates and archetypes

### Available SDK Options

#### 1. EHRbase openEHR SDK (Java)
**Repository**: https://github.com/ehrbase/openEHR_SDK
**Language**: Java
**Status**: Active (v2.27.0, October 2025)

**Features**:
- Entity class generation from openEHR templates with JPA-like annotations
- Bidirectional mapping between entity objects and Archie RM (Reference Model)
- REST client implementation for openEHR API
- AQL query builder and parser
- JSON/XML composition serialization/deserialization
- Template validation engine
- ~20 specialized modules, 2,008 commits

**Limitations**:
- Java-only (incompatible with Python backend)
- Most modules in beta status
- AQL module missing: XOR operations, aggregate functions, pattern matching, path comparisons
- Complex architecture with many dependencies
- Requires Java 11+ runtime

#### 2. pyEHR (Python)
**Repository**: https://github.com/crs4/pyEHR
**Language**: Python
**Status**: Dormant (last active ~2017-2018)

**Features**:
- Multi-backend support (MongoDB, Elasticsearch 1.5)
- Dataset creation and querying
- REST service API
- Archetype model support (JSON format)

**Limitations**:
- **Inactive maintenance**: No recent commits, outdated dependencies
- **Outdated stack**: References Python 2 syntax, Elasticsearch 1.5
- **Different focus**: Designed for secondary data analysis, not primary EHR operations
- **Heavy dependencies**: Requires BaseX XML database, Java 8
- **Not EHRbase-specific**: Generic openEHR support, not optimized for EHRbase REST API

#### 3. Other Python Options
**Status**: None found

Our research found no other actively maintained Python SDKs for openEHR integration. The community discussion in ehrbase/openEHR_SDK#24 (2020) shows Python client libraries were requested but never developed.

## Decision

We will use **httpx directly** to interact with the EHRbase REST API, implementing a lightweight custom `EHRBaseClient` wrapper class.

### Implementation Approach

```python
# api/src/ehrbase/client.py
class EHRBaseClient:
    """Async client for EHRBase REST API."""

    def __init__(self):
        self.base_url = settings.ehrbase_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=httpx.BasicAuth(...),
                headers={"Content-Type": "application/json"}
            )
        return self._client

    async def create_composition(
        self, ehr_id: str, template_id: str,
        composition: dict[str, Any], format: str = "FLAT"
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(
            f"/openehr/v1/ehr/{ehr_id}/composition",
            json=composition,
            params={"templateId": template_id, "format": format}
        )
        response.raise_for_status()
        return response.json()
```

### Architecture

```
api/src/ehrbase/
├── client.py         # EHRBaseClient - thin wrapper around httpx
├── compositions.py   # Composition building helpers
├── queries.py        # AQL query templates and builders
└── templates.py      # Template management utilities
```

## Rationale

### Why Not Java SDK?

1. **Language Mismatch**: Our backend is Python (FastAPI), not Java
2. **Unnecessary Complexity**: We'd need to run a Java service or use JNI/Py4J
3. **Overkill**: We don't need entity generation or complex ORM-like features
4. **Learning Curve**: Understanding 20+ modules vs simple HTTP requests

### Why Not pyEHR?

1. **Inactive Maintenance**: No commits since ~2018, stale dependencies
2. **Outdated Stack**: Python 2 syntax, Elasticsearch 1.5 (current: 8.x)
3. **Wrong Abstraction**: Built for secondary analysis, not primary EHR operations
4. **Heavy Dependencies**: Requires BaseX XML database, Java runtime
5. **Risk**: Unmaintained library could break with Python/dependency updates

### Why Direct httpx?

1. **Simplicity**: EHRbase REST API is well-documented and straightforward
2. **Control**: Full transparency over requests/responses, easy debugging
3. **Async-First**: httpx natively supports async/await (FastAPI best practice)
4. **Maintained**: httpx is actively maintained, widely used, stable
5. **Lightweight**: Single dependency vs complex SDK
6. **Type Safety**: Works seamlessly with Python type hints and mypy
7. **Learning**: For an educational project, understanding the raw API is valuable

### EHRbase REST API Coverage

Our custom client covers all needed endpoints:

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create EHR | `/openehr/v1/ehr` | POST/PUT |
| Get EHR | `/openehr/v1/ehr/{ehr_id}` | GET |
| Create Composition | `/openehr/v1/ehr/{ehr_id}/composition` | POST |
| Get Composition | `/openehr/v1/ehr/{ehr_id}/composition/{uid}` | GET |
| Delete Composition | `/openehr/v1/ehr/{ehr_id}/composition/{uid}` | DELETE |
| AQL Query | `/openehr/v1/query/aql` | POST |
| List Templates | `/openehr/v1/definition/template/adl1.4` | GET |
| Upload Template | `/openehr/v1/definition/template/adl1.4` | POST |

All endpoints are simple HTTP requests with JSON payloads.

## Consequences

### Positive

- **Minimal dependencies**: Only httpx (already used for HTTP requests)
- **Full control**: Direct access to request/response cycle
- **Easy debugging**: Clear request/response logs, no hidden abstractions
- **Type-safe**: Python type hints throughout, mypy validation
- **Future-proof**: Not dependent on unmaintained libraries
- **Educational value**: Learn openEHR API directly vs hidden in SDK
- **Performance**: No SDK overhead, direct HTTP requests
- **Maintainable**: ~150 lines of client code vs thousands in SDK

### Negative

- **Manual work**: Must implement each endpoint method ourselves
- **No validation helpers**: Must manually construct FLAT compositions
- **AQL string-based**: No type-safe query builder (write raw AQL strings)
- **Template handling**: Manual path mapping vs auto-generated classes
- **Maintenance burden**: Must keep up with EHRbase API changes ourselves

### Neutral

- **Testing**: Need to mock HTTP responses (would need mocks for SDK too)
- **Documentation**: Must refer to EHRbase API docs (vs SDK docs)
- **Learning curve**: Need to understand openEHR concepts either way

## Mitigation Strategies

To address the negative consequences:

1. **Composition Builders**: Create helper functions in `compositions.py`
   ```python
   def build_vital_signs_composition(
       systolic: int, diastolic: int, pulse_rate: int,
       recorded_at: datetime
   ) -> dict[str, Any]:
       # Encapsulate FLAT path knowledge
   ```

2. **AQL Templates**: Store common queries in `queries.py` with placeholders
   ```python
   VITAL_SIGNS_QUERY = """
   SELECT ... FROM EHR e CONTAINS COMPOSITION c
   WHERE c/archetype_details/template_id/value = '{template_id}'
   """
   ```

3. **Error Handling**: Centralized HTTP error handling with helpful messages
   ```python
   except httpx.HTTPStatusError as e:
       error_body = e.response.text
       logging.error(f"EHRBase API error: {e.status_code} - {error_body}")
   ```

4. **Type Definitions**: Define Pydantic schemas for all request/response shapes
   ```python
   class VitalSignsCreate(BaseModel):
       patient_id: str
       systolic: int | None
       # ...
   ```

## Alternatives Considered

### 1. Wait for Official Python SDK
**Rejected**: No indication one is being developed. Issue from 2020 still open.

### 2. Fork pyEHR and Update It
**Rejected**: Would need to:
- Port from Python 2 to Python 3
- Update all dependencies (Elasticsearch 1.5 → 8.x)
- Refactor for EHRbase-specific use
- Ongoing maintenance burden equivalent to maintaining SDK

More work than building a focused client.

### 3. Use Java SDK via Py4J or JNI
**Rejected**:
- Adds Java runtime dependency
- Complex inter-process communication
- Performance overhead
- Deployment complexity (Java + Python containers)

### 4. Build Full-Featured Python SDK
**Rejected**: Out of scope for learning project. Would need:
- Template → Python class generation
- Full RM (Reference Model) implementation
- AQL parser and builder
- Months of development

Our focused client is sufficient.

## Migration Path

If Python SDK emerges in the future:

1. **Easy migration**: Our service layer already abstracts EHRbase calls
2. **Incremental adoption**: Can replace methods in `EHRBaseClient` one at a time
3. **No API changes**: Service and router layers remain unchanged

Example:
```python
# Before
result = await ehrbase_client.create_composition(ehr_id, template_id, composition)

# After (hypothetical SDK)
result = await openehr_sdk.composition.create(ehr_id, template_id, composition)
```

Service layer insulates us from client implementation details.

## Related

- ADR-0001: Use openEHR for Clinical Data (chose EHRbase as CDR)
- ADR-0002: FastAPI Backend (async Python framework)
- EHRbase REST API: https://ehrbase.readthedocs.io/en/latest/03_development/04_rest_api/
- httpx documentation: https://www.python-httpx.org/

## References

- EHRbase openEHR_SDK: https://github.com/ehrbase/openEHR_SDK
- pyEHR: https://github.com/crs4/pyEHR
- httpx: https://github.com/encode/httpx
- openEHR REST API specification: https://specifications.openehr.org/releases/ITS-REST/latest/
