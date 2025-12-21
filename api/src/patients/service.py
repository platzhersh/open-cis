from src.db.client import prisma
from src.ehrbase.client import ehrbase_client
from src.patients.schemas import PatientCreate, PatientResponse, PatientUpdate


class PatientService:
    async def create_patient(self, data: PatientCreate) -> PatientResponse:
        """Create a new patient with an EHR in EHRBase."""
        # Create EHR in EHRBase
        ehr_response = await ehrbase_client.create_ehr()
        ehr_id = ehr_response["ehr_id"]["value"]

        # Create patient registry entry in app DB
        patient = await prisma.patientregistry.create(
            data={
                "mrn": data.mrn,
                "ehrId": ehr_id,
                "givenName": data.given_name,
                "familyName": data.family_name,
                "birthDate": data.birth_date,
            }
        )

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )

    async def get_patient(self, patient_id: str) -> PatientResponse | None:
        """Get a patient by ID."""
        patient = await prisma.patientregistry.find_unique(where={"id": patient_id})
        if not patient:
            return None

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )

    async def get_patient_by_mrn(self, mrn: str) -> PatientResponse | None:
        """Get a patient by MRN."""
        patient = await prisma.patientregistry.find_unique(where={"mrn": mrn})
        if not patient:
            return None

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )

    async def list_patients(self, skip: int = 0, limit: int = 100) -> list[PatientResponse]:
        """List all patients with pagination."""
        patients = await prisma.patientregistry.find_many(skip=skip, take=limit)

        return [
            PatientResponse(
                id=p.id,
                mrn=p.mrn,
                ehr_id=p.ehrId,
                given_name=p.givenName,
                family_name=p.familyName,
                birth_date=p.birthDate.date() if p.birthDate else None,
                created_at=p.createdAt,
                updated_at=p.updatedAt,
            )
            for p in patients
        ]

    async def update_patient(self, patient_id: str, data: PatientUpdate) -> PatientResponse | None:
        """Update a patient."""
        update_data = {}
        if data.given_name is not None:
            update_data["givenName"] = data.given_name
        if data.family_name is not None:
            update_data["familyName"] = data.family_name
        if data.birth_date is not None:
            update_data["birthDate"] = data.birth_date

        patient = await prisma.patientregistry.update(
            where={"id": patient_id},
            data=update_data,
        )

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )


patient_service = PatientService()
