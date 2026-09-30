"""Router for vaccination records (CH VACD import/export)."""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.audit.service import log_action
from src.auth.dependencies import get_current_user
from src.auth.permissions import require_role
from src.vaccinations.schemas import ImportResponse, VaccinationListResponse
from src.vaccinations.service import vaccination_service

router = APIRouter()


@router.post("/{patient_id}/vaccinations/import", response_model=ImportResponse)
async def import_vaccinations(
    patient_id: str,
    file: UploadFile = File(...),  # noqa: B008 - CH VACD Bundle (.json) or XDM (.zip)
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
) -> ImportResponse:
    """Import CH VACD documents; re-importing the same Bundle is a no-op."""
    content = await file.read()
    is_zip = content[:2] == b"PK"
    try:
        result = await vaccination_service.import_payload(patient_id, content, is_zip)
    except (ValueError, KeyError) as e:  # bad JSON / zip without METADATA.XML
        raise HTTPException(status_code=422, detail=f"Invalid upload: {e}") from e
    await log_action(
        user_id=current_user.id,
        action="CREATE",
        resource="Vaccination",
        resource_id=patient_id,
    )
    return result


@router.get("/{patient_id}/vaccinations", response_model=VaccinationListResponse)
async def list_vaccinations(
    patient_id: str, current_user=Depends(get_current_user)
) -> VaccinationListResponse:
    """List vaccinations, flagging probable duplicates (same vaccine + date)."""
    return await vaccination_service.list_vaccinations(patient_id)


@router.get("/{patient_id}/vaccinations/export")
async def export_vaccinations(
    patient_id: str, current_user=Depends(get_current_user)
) -> dict[str, Any]:
    """Export all vaccinations as CH VACD document Bundles (one per dose)."""
    bundles = await vaccination_service.export_bundles(patient_id)
    return {"resourceType": "Bundle", "type": "collection", "total": len(bundles),
            "entry": [{"resource": b} for b in bundles]}
