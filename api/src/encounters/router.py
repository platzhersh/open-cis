from fastapi import APIRouter, HTTPException

from src.encounters.schemas import EncounterCreate, EncounterResponse
from src.encounters.service import encounter_service

router = APIRouter()


@router.post("", response_model=EncounterResponse, status_code=201)
async def create_encounter(data: EncounterCreate):
    """Create a new encounter."""
    try:
        return await encounter_service.create_encounter(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/patient/{patient_id}")
async def get_patient_encounters(patient_id: str):
    """Get all encounters for a patient."""
    encounters = await encounter_service.get_encounters_for_patient(patient_id)
    return {"encounters": encounters}
