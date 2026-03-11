"""Router for FHIR terminology operations."""

import logging

from fastapi import APIRouter, HTTPException, Query
from httpx import HTTPStatusError

from src.terminology.client import terminology_client
from src.terminology.schemas import (
    CodeLookupResult,
    SubsumptionResult,
    ValidationResult,
    ValueSetExpansion,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/lookup", response_model=CodeLookupResult)
async def lookup_code(
    system: str = Query(..., description="Terminology system URI (e.g. http://snomed.info/sct)"),
    code: str = Query(..., description="Code to look up"),
) -> CodeLookupResult:
    """Look up a code and return its display name and properties.

    FHIR Operation: CodeSystem/$lookup
    """
    try:
        return await terminology_client.lookup(system=system, code=code)
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Code {code} not found in {system}") from e
        raise HTTPException(status_code=502, detail="Terminology server error") from e
    except Exception as e:
        logger.error(f"Terminology lookup failed: {e}")
        raise HTTPException(status_code=503, detail="Terminology server unavailable") from e


@router.get("/validate", response_model=ValidationResult)
async def validate_code(
    system: str = Query(..., description="Terminology system URI"),
    code: str = Query(..., description="Code to validate"),
    display: str | None = Query(None, description="Expected display name"),
    valueset: str | None = Query(None, description="Value set URL to validate against"),
) -> ValidationResult:
    """Validate that a code exists and optionally belongs to a value set.

    FHIR Operation: CodeSystem/$validate-code or ValueSet/$validate-code
    """
    try:
        return await terminology_client.validate_code(
            system=system, code=code, display=display, value_set_url=valueset
        )
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            return ValidationResult(valid=False, message=f"Code {code} not found in {system}")
        raise HTTPException(status_code=502, detail="Terminology server error") from e
    except Exception as e:
        logger.error(f"Terminology validation failed: {e}")
        raise HTTPException(status_code=503, detail="Terminology server unavailable") from e


@router.get("/expand", response_model=ValueSetExpansion)
async def expand_value_set(
    url: str = Query(..., description="Value set URL to expand"),
    filter: str | None = Query(None, description="Text filter for results"),
    count: int = Query(20, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> ValueSetExpansion:
    """Expand a value set to get all contained codes.

    FHIR Operation: ValueSet/$expand

    Example: ?url=http://snomed.info/sct?fhir_vs=ecl/<73211009&filter=diabetes
    """
    try:
        return await terminology_client.expand_value_set(
            url=url, filter=filter, count=count, offset=offset
        )
    except HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="Terminology server error") from e
    except Exception as e:
        logger.error(f"Terminology expansion failed: {e}")
        raise HTTPException(status_code=503, detail="Terminology server unavailable") from e


@router.get("/search", response_model=ValueSetExpansion)
async def search_terminology(
    system: str = Query(..., description="Terminology system URI"),
    term: str = Query(..., min_length=2, description="Search term (minimum 2 characters)"),
    count: int = Query(20, ge=1, le=1000, description="Maximum results to return"),
) -> ValueSetExpansion:
    """Search for codes matching a term.

    Uses ValueSet/$expand with the code system's implicit value set and a text filter.
    """
    try:
        return await terminology_client.search(system=system, term=term, count=count)
    except HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="Terminology server error") from e
    except Exception as e:
        logger.error(f"Terminology search failed: {e}")
        raise HTTPException(status_code=503, detail="Terminology server unavailable") from e


@router.get("/subsumes", response_model=SubsumptionResult)
async def check_subsumption(
    system: str = Query(..., description="Terminology system URI"),
    code_a: str = Query(..., alias="codeA", description="First code"),
    code_b: str = Query(..., alias="codeB", description="Second code"),
) -> SubsumptionResult:
    """Test subsumption relationship between two codes.

    FHIR Operation: CodeSystem/$subsumes

    Returns outcome: equivalent | subsumes | subsumed-by | not-subsumed
    """
    try:
        return await terminology_client.subsumes(system=system, code_a=code_a, code_b=code_b)
    except HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="Terminology server error") from e
    except Exception as e:
        logger.error(f"Terminology subsumption check failed: {e}")
        raise HTTPException(status_code=503, detail="Terminology server unavailable") from e


@router.get("/health")
async def terminology_health() -> dict:
    """Check terminology server availability."""
    available = await terminology_client.health_check()
    if not available:
        raise HTTPException(status_code=503, detail="Terminology server unavailable")
    return {"status": "available"}
