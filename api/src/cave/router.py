"""Router for CAVE (allergies & adverse reactions)."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.audit.service import log_action
from src.auth.dependencies import get_current_user
from src.auth.permissions import require_role
from src.cave.schemas import (
    CaveEntryCreate,
    CaveEntryResponse,
    CaveEntryUpdate,
    CaveListResponse,
    CaveSummaryResponse,
    NkaRequest,
    NkaResponse,
)
from src.cave.service import cave_service
from src.ehrbase.client import ehrbase_client

router = APIRouter()


@router.post("", response_model=CaveEntryResponse, status_code=201)
async def create_cave_entry(
    data: CaveEntryCreate,
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
) -> CaveEntryResponse:
    """Create a new CAVE entry (allergy/adverse reaction).

    Creates a composition in EHRBase with the adverse reaction data.
    """
    result = await cave_service.create_cave_entry(data)
    await log_action(
        user_id=current_user.id,
        action="CREATE",
        resource="CaveEntry",
        resource_id=result.composition_uid,
    )
    return result


@router.get("", response_model=CaveListResponse)
async def list_cave_entries(
    patient_id: str = Query(..., description="Patient ID (required)"),
    status: str | None = Query(None, description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
    current_user=Depends(get_current_user),
) -> CaveListResponse:
    """List CAVE entries for a patient."""
    return await cave_service.get_cave_entries(
        patient_id=patient_id,
        status=status,
        category=category,
    )


@router.get("/summary/{patient_id}", response_model=CaveSummaryResponse)
async def get_cave_summary(
    patient_id: str, current_user=Depends(get_current_user),
) -> CaveSummaryResponse:
    """Get CAVE summary for the patient banner.

    Returns active allergy count, high criticality flag, and NKA status.
    """
    return await cave_service.get_cave_summary(patient_id)


@router.get("/{composition_uid}", response_model=CaveEntryResponse)
async def get_cave_entry(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
    current_user=Depends(get_current_user),
) -> CaveEntryResponse:
    """Get a single CAVE entry by composition UID."""
    result = await cave_service.get_cave_entry(composition_uid, patient_id)
    if not result:
        raise HTTPException(status_code=404, detail="CAVE entry not found")
    return result


@router.patch("/{composition_uid}", response_model=CaveEntryResponse)
async def update_cave_entry(
    composition_uid: str,
    data: CaveEntryUpdate,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
) -> CaveEntryResponse:
    """Update a CAVE entry (criticality, status, reactions, comment)."""
    result = await cave_service.update_cave_entry(composition_uid, patient_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="CAVE entry not found")
    await log_action(
        user_id=current_user.id,
        action="UPDATE",
        resource="CaveEntry",
        resource_id=composition_uid,
    )
    return result


@router.post("/nka", response_model=NkaResponse, status_code=201)
async def record_nka(
    data: NkaRequest,
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
) -> NkaResponse:
    """Record 'No Known Allergies' for a patient."""
    result = await cave_service.record_nka(data)
    await log_action(
        user_id=current_user.id,
        action="CREATE",
        resource="NKA",
    )
    return result


@router.delete("/nka", status_code=204)
async def remove_nka(
    patient_id: str = Query(..., description="Patient ID"),
    current_user=require_role("ADMIN", "CLINICIAN"),
) -> None:
    """Remove 'No Known Allergies' declaration for a patient."""
    success = await cave_service.remove_nka(patient_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="No NKA declaration found for this patient"
        )
    await log_action(
        user_id=current_user.id,
        action="DELETE",
        resource="NKA",
    )


@router.delete("/{composition_uid}", status_code=204)
async def delete_cave_entry(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
    current_user=require_role("ADMIN", "CLINICIAN"),
) -> None:
    """Delete a CAVE entry composition."""
    success = await cave_service.delete_cave_entry(composition_uid, patient_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="CAVE entry not found or delete failed"
        )
    await log_action(
        user_id=current_user.id,
        action="DELETE",
        resource="CaveEntry",
        resource_id=composition_uid,
    )


@router.get("/debug/webtemplate")
async def debug_webtemplate(current_user=Depends(get_current_user)) -> dict:
    """Debug endpoint: show web template paths and FLAT example for CAVE template.

    Returns the web template tree (with FLAT IDs) and an example FLAT composition
    so we can verify the correct path structure.
    """
    template_id = cave_service.TEMPLATE_ID

    web_template = await ehrbase_client.get_web_template(template_id)
    flat_example = await ehrbase_client.get_flat_example(template_id)

    # Extract FLAT paths from the web template tree
    flat_paths: list[str] = []
    tree = (
        web_template.get("webTemplate", {}).get("tree")
        or web_template.get("tree")
    )
    if tree:
        stack: list[tuple[dict, str]] = [(tree, "")]
        while stack:
            node, prefix = stack.pop()
            node_id = node.get("id", "")
            rm_type = node.get("rmType", "")
            current = f"{prefix}/{node_id}" if prefix else node_id
            flat_paths.append(f"{current} ({rm_type})")
            for child in reversed(node.get("children", [])):
                stack.append((child, current))

    return {
        "template_id": template_id,
        "web_template_flat_paths": flat_paths,
        "flat_example_keys": sorted(flat_example.keys())
        if isinstance(flat_example, dict) and "error" not in flat_example
        else flat_example,
        "flat_example": flat_example,
    }
