"""Router for vital signs observations with openEHR transparency."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from src.ehrbase.client import ehrbase_client
from src.observations.schemas import (
    RawCompositionResponse,
    TemplateInfo,
    TemplateListResponse,
    VitalSignsCreate,
    VitalSignsListResponse,
    VitalSignsResponse,
)
from src.observations.service import observation_service

router = APIRouter()


# ============================================================================
# Vital Signs CRUD
# ============================================================================


@router.post("/vital-signs", response_model=VitalSignsResponse, status_code=201)
async def record_vital_signs(data: VitalSignsCreate) -> VitalSignsResponse:
    """Record vital signs for a patient.

    Creates a composition in EHRBase with the vital signs data.
    Returns the recorded data with openEHR metadata for transparency.
    """
    try:
        return await observation_service.record_vital_signs(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/vital-signs", response_model=VitalSignsListResponse)
async def list_vital_signs(
    patient_id: str = Query(..., description="Patient ID (required)"),
    from_date: datetime | None = Query(None, description="Start of date range"),
    to_date: datetime | None = Query(None, description="End of date range"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Page size"),
) -> VitalSignsListResponse:
    """List vital signs for a patient.

    Returns paginated list of vital signs readings with openEHR metadata.
    """
    return await observation_service.get_vital_signs_for_patient(
        patient_id=patient_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )


@router.get("/vital-signs/{composition_uid}", response_model=VitalSignsResponse)
async def get_vital_signs(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
) -> VitalSignsResponse:
    """Get a single vital signs reading by composition UID."""
    result = await observation_service.get_vital_signs(composition_uid, patient_id)
    if not result:
        raise HTTPException(status_code=404, detail="Vital signs not found")
    return result


@router.delete("/vital-signs/{composition_uid}", status_code=204)
async def delete_vital_signs(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
) -> None:
    """Delete a vital signs composition."""
    success = await observation_service.delete_vital_signs(composition_uid, patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vital signs not found or delete failed")


# ============================================================================
# openEHR Transparency Endpoints
# ============================================================================


@router.get("/openehr/templates", response_model=TemplateListResponse)
async def list_templates() -> TemplateListResponse:
    """List all available operational templates in EHRBase."""
    try:
        templates = await ehrbase_client.list_templates()
        return TemplateListResponse(
            templates=[
                TemplateInfo(
                    template_id=t.get("template_id", ""),
                    concept=t.get("concept"),
                    archetype_id=t.get("archetype_id"),
                )
                for t in templates
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Failed to fetch templates: {e}"
        ) from e


@router.get("/openehr/templates/{template_id}")
async def get_template_info(template_id: str) -> dict:
    """Get detailed information about a template.

    Returns the template structure with example paths.
    """
    try:
        example = await ehrbase_client.get_template_example(template_id, format="FLAT")
        return {
            "template_id": template_id,
            "format": "FLAT",
            "example": example,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Failed to fetch template: {e}"
        ) from e


@router.get("/openehr/compositions/{composition_uid}", response_model=RawCompositionResponse)
async def get_raw_composition(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
    format: Literal["FLAT", "STRUCTURED"] = Query("FLAT", description="Composition format"),
) -> RawCompositionResponse:
    """Get raw composition data for transparency.

    Returns the full composition in the requested format (FLAT or STRUCTURED).
    """
    result = await observation_service.get_raw_composition(
        composition_uid, patient_id, format
    )
    if not result:
        raise HTTPException(status_code=404, detail="Composition not found")
    return RawCompositionResponse(**result)


@router.get("/openehr/compositions/{composition_uid}/paths")
async def get_composition_paths(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
) -> dict:
    """Get all paths in a composition for transparency.

    Returns a flattened list of all paths and values in the composition.
    """
    result = await observation_service.get_raw_composition(
        composition_uid, patient_id, "FLAT"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Composition not found")

    composition = result.get("composition", {})
    paths = []

    for path, value in composition.items():
        paths.append(
            {
                "path": path,
                "value": value,
                "type": type(value).__name__,
            }
        )

    return {
        "composition_uid": composition_uid,
        "template_id": result.get("template_id"),
        "paths": sorted(paths, key=lambda x: x["path"]),
    }


@router.get("/openehr/archetypes/{archetype_id}")
async def get_archetype_info(archetype_id: str) -> dict:
    """Get information about an archetype.

    Provides archetype details and link to Clinical Knowledge Manager (CKM).
    """
    # Parse archetype ID to construct CKM URL
    # Format: openEHR-EHR-OBSERVATION.blood_pressure.v2
    parts = archetype_id.split(".")
    if len(parts) >= 2:
        concept = parts[-2]  # e.g., "blood_pressure"
    else:
        concept = archetype_id

    # Known archetype mappings (supports both v1 and v2 versions)
    ckm_links = {
        "openEHR-EHR-OBSERVATION.blood_pressure.v1": "https://ckm.openehr.org/ckm/archetypes/1013.1.3574",
        "openEHR-EHR-OBSERVATION.blood_pressure.v2": "https://ckm.openehr.org/ckm/archetypes/1013.1.3574",
        "openEHR-EHR-OBSERVATION.pulse.v1": "https://ckm.openehr.org/ckm/archetypes/1013.1.4295",
        "openEHR-EHR-OBSERVATION.pulse.v2": "https://ckm.openehr.org/ckm/archetypes/1013.1.4295",
        "openEHR-EHR-COMPOSITION.encounter.v1": "https://ckm.openehr.org/ckm/archetypes/1013.1.120",
    }

    descriptions = {
        "openEHR-EHR-OBSERVATION.blood_pressure.v1": (
            "The local systemic arterial blood pressure which is a surrogate "
            "for arterial pressure in the systemic circulation."
        ),
        "openEHR-EHR-OBSERVATION.blood_pressure.v2": (
            "The local systemic arterial blood pressure which is a surrogate "
            "for arterial pressure in the systemic circulation."
        ),
        "openEHR-EHR-OBSERVATION.pulse.v1": (
            "The rate and associated attributes for a pulse or heart beat."
        ),
        "openEHR-EHR-OBSERVATION.pulse.v2": (
            "The rate and associated attributes for a pulse or heart beat."
        ),
        "openEHR-EHR-COMPOSITION.encounter.v1": (
            "Interaction, contact or care event between a subject of care "
            "and healthcare provider(s)."
        ),
    }

    return {
        "archetype_id": archetype_id,
        "concept": concept,
        "description": descriptions.get(archetype_id, "No description available"),
        "ckm_url": ckm_links.get(archetype_id),
        "reference_model": "EHR" if "EHR-" in archetype_id else "DEMOGRAPHIC",
        "type": parts[0].split("-")[-1] if "-" in parts[0] else "UNKNOWN",
    }
