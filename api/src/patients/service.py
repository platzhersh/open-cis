from datetime import UTC, date, datetime

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
                "birthDate": datetime.combine(
                    date.fromisoformat(data.birth_date), datetime.min.time()
                )
                if data.birth_date
                else None,
            }
        )

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date().isoformat() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )

    async def get_patient(self, patient_id: str) -> PatientResponse | None:
        """Get a patient by ID (excludes soft-deleted)."""
        patient = await prisma.patientregistry.find_first(
            where={"id": patient_id, "deletedAt": None}
        )
        if not patient:
            return None

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date().isoformat() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )

    async def get_patient_by_mrn(self, mrn: str) -> PatientResponse | None:
        """Get a patient by MRN (excludes soft-deleted)."""
        patient = await prisma.patientregistry.find_first(
            where={"mrn": mrn, "deletedAt": None}
        )
        if not patient:
            return None

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date().isoformat() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )

    async def list_patients(
        self, skip: int = 0, limit: int = 100, include_deleted: bool = False
    ) -> list[PatientResponse]:
        """List all patients with pagination, excluding soft-deleted by default."""
        where_clause = {} if include_deleted else {"deletedAt": None}
        patients = await prisma.patientregistry.find_many(
            where=where_clause,  # type: ignore[arg-type]
            skip=skip,
            take=limit,
            order={"createdAt": "desc"},
        )

        return [
            PatientResponse(
                id=p.id,
                mrn=p.mrn,
                ehr_id=p.ehrId,
                given_name=p.givenName,
                family_name=p.familyName,
                birth_date=p.birthDate.date().isoformat() if p.birthDate else None,
                created_at=p.createdAt,
                updated_at=p.updatedAt,
            )
            for p in patients
        ]

    async def mrn_exists(self, mrn: str) -> bool:
        """Check if MRN already exists (excluding soft-deleted patients)."""
        patient = await prisma.patientregistry.find_first(
            where={"mrn": mrn, "deletedAt": None}
        )
        return patient is not None

    async def delete_patient(self, patient_id: str) -> bool:
        """Soft delete a patient by setting deletedAt timestamp."""
        patient = await prisma.patientregistry.find_unique(where={"id": patient_id})
        if not patient or patient.deletedAt is not None:
            return False

        await prisma.patientregistry.update(
            where={"id": patient_id},
            data={"deletedAt": datetime.now(UTC)},
        )
        return True

    async def update_patient(self, patient_id: str, data: PatientUpdate) -> PatientResponse | None:
        """Update a patient."""
        update_data: dict[str, str | datetime | None] = {}
        if data.given_name is not None:
            update_data["givenName"] = data.given_name
        if data.family_name is not None:
            update_data["familyName"] = data.family_name
        if data.birth_date is not None:
            update_data["birthDate"] = datetime.combine(
                date.fromisoformat(data.birth_date), datetime.min.time()
            )

        patient = await prisma.patientregistry.update(
            where={"id": patient_id},
            data=update_data,  # type: ignore[arg-type]
        )

        if patient is None:
            return None

        return PatientResponse(
            id=patient.id,
            mrn=patient.mrn,
            ehr_id=patient.ehrId,
            given_name=patient.givenName,
            family_name=patient.familyName,
            birth_date=patient.birthDate.date().isoformat() if patient.birthDate else None,
            created_at=patient.createdAt,
            updated_at=patient.updatedAt,
        )


patient_service = PatientService()
