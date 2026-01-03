from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from src.encounters.schemas import (
    EncounterCreate,
    EncounterResponse,
    EncounterUpdate,
)
from src.encounters.service import encounter_service

router = APIRouter()


@router.post("", response_model=EncounterResponse, status_code=201)
async def create_encounter(data: EncounterCreate):
    """Create a new encounter."""
    try:
        return await encounter_service.create_encounter(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[EncounterResponse])
async def list_encounters(
    patient_id: str | None = Query(None, description="Filter by patient ID"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_deleted: bool = Query(False, description="Include soft-deleted encounters"),
):
    """List encounters with optional filtering."""
    return await encounter_service.list_encounters(
        patient_id=patient_id,
        status=status,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
    )


@router.get("/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(encounter_id: str):
    """Get an encounter by ID."""
    encounter = await encounter_service.get_encounter(encounter_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter


@router.patch("/{encounter_id}", response_model=EncounterResponse)
async def update_encounter(encounter_id: str, data: EncounterUpdate):
    """Update an encounter."""
    try:
        encounter = await encounter_service.update_encounter(encounter_id, data)
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        return encounter
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{encounter_id}", status_code=204)
async def delete_encounter(encounter_id: str):
    """Soft delete an encounter."""
    deleted = await encounter_service.delete_encounter(encounter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return Response(status_code=204)
