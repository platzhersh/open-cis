"""Patient data access layer."""

from src.db.client import prisma


async def find_patient_by_id(patient_id: str):
    """Find a patient by ID."""
    return await prisma.patientregistry.find_unique(where={"id": patient_id})


async def find_patient_by_mrn(mrn: str):
    """Find a patient by MRN."""
    return await prisma.patientregistry.find_unique(where={"mrn": mrn})


async def find_patient_by_ehr_id(ehr_id: str):
    """Find a patient by EHR ID."""
    return await prisma.patientregistry.find_unique(where={"ehrId": ehr_id})


async def find_all_patients(skip: int = 0, limit: int = 100):
    """Find all patients with pagination."""
    return await prisma.patientregistry.find_many(skip=skip, take=limit)


async def create_patient(data: dict):
    """Create a new patient."""
    return await prisma.patientregistry.create(data=data)


async def update_patient(patient_id: str, data: dict):
    """Update a patient."""
    return await prisma.patientregistry.update(where={"id": patient_id}, data=data)


async def delete_patient(patient_id: str):
    """Delete a patient."""
    return await prisma.patientregistry.delete(where={"id": patient_id})
