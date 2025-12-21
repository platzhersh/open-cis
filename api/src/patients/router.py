from fastapi import APIRouter, HTTPException, Query

from src.patients.schemas import PatientCreate, PatientUpdate, PatientResponse
from src.patients.service import patient_service

router = APIRouter()


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(data: PatientCreate):
    """Create a new patient."""
    return await patient_service.create_patient(data)


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all patients."""
    return await patient_service.list_patients(skip=skip, limit=limit)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """Get a patient by ID."""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/mrn/{mrn}", response_model=PatientResponse)
async def get_patient_by_mrn(mrn: str):
    """Get a patient by MRN."""
    patient = await patient_service.get_patient_by_mrn(mrn)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: str, data: PatientUpdate):
    """Update a patient."""
    patient = await patient_service.update_patient(patient_id, data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
