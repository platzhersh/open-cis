"""Router for vital signs observations with openEHR transparency."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from src.audit.service import log_action
from src.auth.dependencies import get_current_user
from src.auth.permissions import require_role
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
async def record_vital_signs(
    data: VitalSignsCreate,
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
) -> VitalSignsResponse:
    """Record vital signs for a patient.

    Creates a composition in EHRBase with the vital signs data.
    Returns the recorded data with openEHR metadata for transparency.
    """
    result = await observation_service.record_vital_signs(data)
    await log_action(
        user_id=current_user.id,
        action="CREATE",
        resource="VitalSigns",
        resource_id=result.composition_uid,
    )
    return result


@router.get("/vital-signs", response_model=VitalSignsListResponse)
async def list_vital_signs(
    patient_id: str = Query(..., description="Patient ID (required)"),
    from_date: datetime | None = Query(None, description="Start of date range"),
    to_date: datetime | None = Query(None, description="End of date range"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Page size"),
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
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
    current_user=require_role("ADMIN", "CLINICIAN"),
) -> None:
    """Delete a vital signs composition."""
    success = await observation_service.delete_vital_signs(composition_uid, patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vital signs not found or delete failed")
    await log_action(
        user_id=current_user.id,
        action="DELETE",
        resource="VitalSigns",
        resource_id=composition_uid,
    )


# ============================================================================
# openEHR Transparency Endpoints
# ============================================================================


@router.get("/openehr/templates", response_model=TemplateListResponse)
async def list_templates(current_user=Depends(get_current_user)) -> TemplateListResponse:
    """List all available operational templates in EHRBase."""
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


@router.get("/openehr/templates/{template_id}")
async def get_template_info(template_id: str, current_user=Depends(get_current_user)) -> dict:
    """Get detailed information about a template.

    Returns the template structure with example paths.
    """
    example = await ehrbase_client.get_template_example(template_id, format="FLAT")
    return {
        "template_id": template_id,
        "format": "FLAT",
        "example": example,
    }


@router.get("/openehr/templates/{template_id}/webtemplate")
async def get_web_template(template_id: str, current_user=Depends(get_current_user)) -> dict:
    """Get the web template JSON showing all valid FLAT paths.

    Useful for debugging FLAT format composition building issues.
    """
    web_template = await ehrbase_client.get_web_template(template_id)

    # Extract FLAT paths from the web template tree if available
    flat_paths: list[str] = []
    tree = web_template.get("webTemplate", {}).get("tree") or web_template.get("tree")
    if tree:

        def extract_paths(node: dict, prefix: str = "") -> None:
            node_id = node.get("id", "")
            current = f"{prefix}/{node_id}" if prefix else node_id
            rm_type = node.get("rmType", "")
            flat_paths.append(f"{current} ({rm_type})")
            for child in node.get("children", []):
                extract_paths(child, current)

        extract_paths(tree)

    return {
        "template_id": template_id,
        "flat_paths": flat_paths,
        "raw": web_template,
    }


@router.get("/openehr/compositions/{composition_uid}", response_model=RawCompositionResponse)
async def get_raw_composition(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
    format: Literal["FLAT", "STRUCTURED"] = Query("FLAT", description="Composition format"),
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
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
async def get_archetype_info(archetype_id: str, current_user=Depends(get_current_user)) -> dict:
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
