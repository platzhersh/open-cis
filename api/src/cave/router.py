"""Router for CAVE (allergies & adverse reactions)."""

from fastapi import APIRouter, HTTPException, Query

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

router = APIRouter()


@router.post("", response_model=CaveEntryResponse, status_code=201)
async def create_cave_entry(data: CaveEntryCreate) -> CaveEntryResponse:
    """Create a new CAVE entry (allergy/adverse reaction).

    Creates a composition in EHRBase with the adverse reaction data.
    """
    return await cave_service.create_cave_entry(data)


@router.get("", response_model=CaveListResponse)
async def list_cave_entries(
    patient_id: str = Query(..., description="Patient ID (required)"),
    status: str | None = Query(None, description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
) -> CaveListResponse:
    """List CAVE entries for a patient."""
    return await cave_service.get_cave_entries(
        patient_id=patient_id,
        status=status,
        category=category,
    )


@router.get("/summary/{patient_id}", response_model=CaveSummaryResponse)
async def get_cave_summary(patient_id: str) -> CaveSummaryResponse:
    """Get CAVE summary for the patient banner.

    Returns active allergy count, high criticality flag, and NKA status.
    """
    return await cave_service.get_cave_summary(patient_id)


@router.get("/{composition_uid}", response_model=CaveEntryResponse)
async def get_cave_entry(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
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
) -> CaveEntryResponse:
    """Update a CAVE entry (criticality, status, reactions, comment)."""
    result = await cave_service.update_cave_entry(composition_uid, patient_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="CAVE entry not found")
    return result


@router.delete("/{composition_uid}", status_code=204)
async def delete_cave_entry(
    composition_uid: str,
    patient_id: str = Query(..., description="Patient ID for EHR lookup"),
) -> None:
    """Delete a CAVE entry composition."""
    success = await cave_service.delete_cave_entry(composition_uid, patient_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="CAVE entry not found or delete failed"
        )


@router.post("/nka", response_model=NkaResponse, status_code=201)
async def record_nka(data: NkaRequest) -> NkaResponse:
    """Record 'No Known Allergies' for a patient."""
    return await cave_service.record_nka(data)
