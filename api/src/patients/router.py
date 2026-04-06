from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.audit.service import log_action
from src.auth.dependencies import get_current_user
from src.auth.permissions import require_role
from src.patients.schemas import (
    MrnExistsResponse,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from src.patients.service import patient_service

router = APIRouter()


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    data: PatientCreate,
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
):
    """Create a new patient."""
    patient = await patient_service.create_patient(data)
    await log_action(
        user_id=current_user.id,
        action="CREATE",
        resource="Patient",
        resource_id=patient.id,
        ehr_id=patient.ehrId,
    )
    return patient


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_deleted: bool = Query(False, description="Include soft-deleted patients"),
    current_user=Depends(get_current_user),
):
    """List all patients (excludes soft-deleted by default)."""
    return await patient_service.list_patients(
        skip=skip, limit=limit, include_deleted=include_deleted
    )


@router.get("/mrn/{mrn}/exists", response_model=MrnExistsResponse)
async def check_mrn_exists(mrn: str, current_user=Depends(get_current_user)):
    """Check if MRN already exists (for validation)."""
    exists = await patient_service.mrn_exists(mrn)
    return MrnExistsResponse(exists=exists)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, current_user=Depends(get_current_user)):
    """Get a patient by ID."""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/mrn/{mrn}", response_model=PatientResponse)
async def get_patient_by_mrn(mrn: str, current_user=Depends(get_current_user)):
    """Get a patient by MRN."""
    patient = await patient_service.get_patient_by_mrn(mrn)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    current_user=require_role("ADMIN", "CLINICIAN", "NURSE"),
):
    """Update a patient."""
    patient = await patient_service.update_patient(patient_id, data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await log_action(
        user_id=current_user.id,
        action="UPDATE",
        resource="Patient",
        resource_id=patient_id,
    )
    return patient


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: str,
    current_user=require_role("ADMIN"),
):
    """Soft delete a patient. Requires ADMIN role."""
    deleted = await patient_service.delete_patient(patient_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Patient not found")
    await log_action(
        user_id=current_user.id,
        action="DELETE",
        resource="Patient",
        resource_id=patient_id,
    )
    return Response(status_code=204)
