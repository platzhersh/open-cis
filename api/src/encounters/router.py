from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.audit.service import log_action
from src.auth.dependencies import get_current_user
from src.auth.permissions import require_role
from src.encounters.schemas import (
    EncounterCreate,
    EncounterResponse,
    EncounterUpdate,
)
from src.encounters.service import encounter_service

router = APIRouter()


@router.post("", response_model=EncounterResponse, status_code=201)
async def create_encounter(
    data: EncounterCreate,
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
):
    """Create a new encounter."""
    try:
        encounter = await encounter_service.create_encounter(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await log_action(
        user_id=current_user.id,
        action="CREATE",
        resource="Encounter",
        resource_id=encounter.id,
    )
    return encounter


@router.get("", response_model=list[EncounterResponse])
async def list_encounters(
    patient_id: str | None = Query(None, description="Filter by patient ID"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_deleted: bool = Query(False, description="Include soft-deleted encounters"),
    current_user=Depends(get_current_user),
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
async def get_encounter(encounter_id: str, current_user=Depends(get_current_user)):
    """Get an encounter by ID."""
    encounter = await encounter_service.get_encounter(encounter_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter


@router.patch("/{encounter_id}", response_model=EncounterResponse)
async def update_encounter(
    encounter_id: str,
    data: EncounterUpdate,
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
):
    """Update an encounter."""
    try:
        encounter = await encounter_service.update_encounter(encounter_id, data)
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await log_action(
        user_id=current_user.id,
        action="UPDATE",
        resource="Encounter",
        resource_id=encounter_id,
    )
    return encounter


@router.delete("/{encounter_id}", status_code=204)
async def delete_encounter(
    encounter_id: str,
    current_user=require_role("ADMIN", "CLINICIAN"),
):
    """Soft delete an encounter."""
    deleted = await encounter_service.delete_encounter(encounter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Encounter not found")
    await log_action(
        user_id=current_user.id,
        action="DELETE",
        resource="Encounter",
        resource_id=encounter_id,
    )
    return Response(status_code=204)
