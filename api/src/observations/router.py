from fastapi import APIRouter, HTTPException

from src.observations.schemas import VitalSignsCreate, VitalSignsResponse
from src.observations.service import observation_service

router = APIRouter()


@router.post("/vital-signs", response_model=VitalSignsResponse, status_code=201)
async def record_vital_signs(data: VitalSignsCreate):
    """Record vital signs for a patient."""
    try:
        return await observation_service.record_vital_signs(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/vital-signs/patient/{patient_id}")
async def get_patient_vital_signs(patient_id: str):
    """Get all vital signs for a patient."""
    vital_signs = await observation_service.get_vital_signs_for_patient(patient_id)
    return {"vital_signs": vital_signs}
