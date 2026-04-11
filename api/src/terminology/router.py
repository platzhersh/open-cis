"""Terminology API endpoints: health check and FHIR pass-through."""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.config import settings
from src.terminology.client import terminology_client
from src.terminology.schemas import CodeLookupResponse, TerminologyHealthResponse

router = APIRouter()


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health", response_model=TerminologyHealthResponse)
async def terminology_health() -> TerminologyHealthResponse:
    """Check connectivity to the upstream FHIR terminology server."""
    if not settings.terminology_enabled:
        return TerminologyHealthResponse(
            status="offline", url=settings.terminology_server_url, response_ms=None
        )

    status, response_ms = await terminology_client.health_check()
    return TerminologyHealthResponse(
        status=status,
        url=settings.terminology_server_url,
        response_ms=response_ms,
    )


# ============================================================================
# FHIR Pass-Through Endpoints
# ============================================================================


fhir_router = APIRouter()


@fhir_router.get("/CodeSystem/$lookup", response_model=CodeLookupResponse)
async def code_lookup(
    system: str = Query(..., description="Code system URI (e.g. http://snomed.info/sct)"),
    code: str = Query(..., description="Code to look up"),
) -> CodeLookupResponse:
    """Look up a code's display term via the upstream terminology server."""
    display = await terminology_client.lookup(system, code)
    return CodeLookupResponse(
        system=system,
        code=code,
        display=display,
        found=display is not None,
    )


@fhir_router.get("/ValueSet/$expand")
async def valueset_expand(
    url: str = Query(..., description="Canonical ValueSet URL"),
    filter: str | None = Query(None, description="Text filter for expansion"),
    count: int = Query(200, ge=1, le=1000, description="Max concepts to return"),
) -> JSONResponse:
    """Expand a ValueSet via the upstream terminology server.

    Returns raw FHIR ValueSet JSON for direct consumption by medblocks-ui components.
    """
    result = await terminology_client.expand(url, filter=filter, count=count)
    return JSONResponse(content=result, media_type="application/fhir+json")


@fhir_router.get("/ValueSet/{value_set_id}/$expand")
async def valueset_expand_by_id(
    value_set_id: str,
    filter: str | None = Query(None, description="Text filter for expansion"),
    count: int = Query(200, ge=1, le=1000, description="Max concepts to return"),
) -> JSONResponse:
    """Expand a ValueSet by ID via the upstream terminology server.

    Proxies to the upstream server's ValueSet/{id}/$expand endpoint.
    """
    try:
        client = terminology_client._ensure_client()
        params: dict[str, str | int] = {"count": count}
        if filter:
            params["filter"] = filter

        response = await client.get(f"/ValueSet/{value_set_id}/$expand", params=params)
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            media_type="application/fhir+json",
        )
    except Exception as e:
        return JSONResponse(
            content={
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": str(e),
                }],
            },
            status_code=502,
            media_type="application/fhir+json",
        )


@fhir_router.get("/ValueSet/$validate-code")
async def valueset_validate_code(
    url: str = Query(..., description="Canonical ValueSet URL"),
    system: str = Query(..., description="Code system URI"),
    code: str = Query(..., description="Code to validate"),
) -> JSONResponse:
    """Validate whether a code belongs to a ValueSet.

    Returns a FHIR Parameters response.
    """
    result = await terminology_client.validate_code(url, system, code)
    return JSONResponse(
        content={
            "resourceType": "Parameters",
            "parameter": [{"name": "result", "valueBoolean": result}],
        },
        media_type="application/fhir+json",
    )
