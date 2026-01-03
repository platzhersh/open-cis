from datetime import datetime

from src.db.client import prisma
from src.encounters.schemas import (
    EncounterCreate,
    EncounterResponse,
    EncounterStatus,
    EncounterUpdate,
)


class EncounterService:
    """Service for encounter operations."""

    async def create_encounter(self, data: EncounterCreate) -> EncounterResponse:
        """Create a new encounter."""
        # Validate that finished encounters have end_time
        if data.status == EncounterStatus.FINISHED and data.end_time is None:
            raise ValueError("Finished encounters must have an end_time")

        encounter = await prisma.encounter.create(
            data={
                "patientId": data.patient_id,
                "type": data.type.value,
                "status": data.status.value,
                "startTime": data.start_time,
                "endTime": data.end_time,
                "reason": data.reason,
                "providerName": data.provider_name,
                "location": data.location,
            }
        )

        return EncounterResponse(
            id=encounter.id,
            patient_id=encounter.patientId,
            type=encounter.type,
            status=encounter.status,
            start_time=encounter.startTime,
            end_time=encounter.endTime,
            reason=encounter.reason,
            provider_name=encounter.providerName,
            location=encounter.location,
            created_at=encounter.createdAt,
            updated_at=encounter.updatedAt,
        )

    async def get_encounter(self, encounter_id: str) -> EncounterResponse | None:
        """Get an encounter by ID (excludes soft-deleted)."""
        encounter = await prisma.encounter.find_first(
            where={"id": encounter_id, "deletedAt": None}
        )
        if not encounter:
            return None

        return EncounterResponse(
            id=encounter.id,
            patient_id=encounter.patientId,
            type=encounter.type,
            status=encounter.status,
            start_time=encounter.startTime,
            end_time=encounter.endTime,
            reason=encounter.reason,
            provider_name=encounter.providerName,
            location=encounter.location,
            created_at=encounter.createdAt,
            updated_at=encounter.updatedAt,
        )

    async def list_encounters(
        self,
        patient_id: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[EncounterResponse]:
        """List encounters with optional filtering."""
        where_clause = {} if include_deleted else {"deletedAt": None}

        if patient_id:
            where_clause["patientId"] = patient_id
        if status:
            where_clause["status"] = status

        encounters = await prisma.encounter.find_many(
            where=where_clause,
            skip=skip,
            take=limit,
            order={"startTime": "desc"},
        )

        return [
            EncounterResponse(
                id=e.id,
                patient_id=e.patientId,
                type=e.type,
                status=e.status,
                start_time=e.startTime,
                end_time=e.endTime,
                reason=e.reason,
                provider_name=e.providerName,
                location=e.location,
                created_at=e.createdAt,
                updated_at=e.updatedAt,
            )
            for e in encounters
        ]

    async def update_encounter(
        self, encounter_id: str, data: EncounterUpdate
    ) -> EncounterResponse | None:
        """Update an encounter."""
        # Build update dict only with provided fields
        update_data: dict = {}
        if data.type is not None:
            update_data["type"] = data.type.value
        if data.status is not None:
            update_data["status"] = data.status.value
            # Validate finished status has end_time
            if data.status == EncounterStatus.FINISHED and data.end_time is None:
                # Check if encounter already has end_time
                existing = await prisma.encounter.find_unique(
                    where={"id": encounter_id}
                )
                if existing and existing.endTime is None:
                    raise ValueError("Finished encounters must have an end_time")
        if data.start_time is not None:
            update_data["startTime"] = data.start_time
        if data.end_time is not None:
            update_data["endTime"] = data.end_time
        if data.reason is not None:
            update_data["reason"] = data.reason
        if data.provider_name is not None:
            update_data["providerName"] = data.provider_name
        if data.location is not None:
            update_data["location"] = data.location

        try:
            encounter = await prisma.encounter.update(
                where={"id": encounter_id}, data=update_data
            )
        except Exception:
            return None

        return EncounterResponse(
            id=encounter.id,
            patient_id=encounter.patientId,
            type=encounter.type,
            status=encounter.status,
            start_time=encounter.startTime,
            end_time=encounter.endTime,
            reason=encounter.reason,
            provider_name=encounter.providerName,
            location=encounter.location,
            created_at=encounter.createdAt,
            updated_at=encounter.updatedAt,
        )

    async def delete_encounter(self, encounter_id: str) -> bool:
        """Soft delete an encounter."""
        encounter = await prisma.encounter.find_unique(where={"id": encounter_id})
        if not encounter or encounter.deletedAt is not None:
            return False

        await prisma.encounter.update(
            where={"id": encounter_id},
            data={"deletedAt": datetime.utcnow()},
        )
        return True


encounter_service = EncounterService()
