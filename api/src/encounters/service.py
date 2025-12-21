"""Encounter service for managing clinical encounters."""

from datetime import datetime
from typing import Any

from src.ehrbase.client import ehrbase_client
from src.ehrbase.queries import ENCOUNTERS_QUERY
from src.patients.repository import find_patient_by_id
from src.encounters.schemas import EncounterCreate, EncounterResponse


class EncounterService:
    async def create_encounter(self, data: EncounterCreate) -> EncounterResponse:
        """Create a new encounter for a patient."""
        # Get patient to retrieve EHR ID
        patient = await find_patient_by_id(data.patient_id)
        if not patient:
            raise ValueError("Patient not found")

        start_time = data.start_time or datetime.utcnow()

        # For now, return a placeholder - composition creation requires templates
        return EncounterResponse(
            id="pending",
            patient_id=data.patient_id,
            ehr_id=patient.ehrId,
            composition_uid=None,
            encounter_type=data.encounter_type,
            start_time=start_time,
            end_time=None,
            notes=data.notes,
        )

    async def get_encounters_for_patient(self, patient_id: str) -> list[dict[str, Any]]:
        """Get all encounters for a patient using AQL."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return []

        result = await ehrbase_client.execute_aql(
            ENCOUNTERS_QUERY,
            parameters={"ehr_id": patient.ehrId}
        )

        return result.get("rows", [])


encounter_service = EncounterService()
