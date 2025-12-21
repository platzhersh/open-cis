from fastapi import APIRouter, HTTPException

from src.medications.schemas import MedicationOrderCreate, MedicationOrderResponse
from src.medications.service import medication_service

router = APIRouter()


@router.post("", response_model=MedicationOrderResponse, status_code=201)
async def create_medication_order(data: MedicationOrderCreate):
    """Create a new medication order."""
    try:
        return await medication_service.create_medication_order(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/patient/{patient_id}")
async def get_patient_medications(patient_id: str):
    """Get all medication orders for a patient."""
    medications = await medication_service.get_medications_for_patient(patient_id)
    return {"medications": medications}
