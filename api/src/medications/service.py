"""Medication service for managing prescriptions."""

from datetime import UTC, datetime
from typing import Any

from src.ehrbase.client import ehrbase_client
from src.ehrbase.queries import MEDICATIONS_QUERY
from src.medications.schemas import MedicationOrderCreate, MedicationOrderResponse
from src.patients.repository import find_patient_by_id


class MedicationService:
    async def create_medication_order(self, data: MedicationOrderCreate) -> MedicationOrderResponse:
        """Create a new medication order for a patient."""
        patient = await find_patient_by_id(data.patient_id)
        if not patient:
            raise ValueError("Patient not found")

        # For now, return a placeholder - composition creation requires templates
        return MedicationOrderResponse(
            composition_uid=None,
            patient_id=data.patient_id,
            medication_name=data.medication_name,
            dose=data.dose,
            dose_unit=data.dose_unit,
            frequency=data.frequency,
            route=data.route,
            instructions=data.instructions,
            ordered_at=datetime.now(UTC),
            status="active",
        )

    async def get_medications_for_patient(self, patient_id: str) -> list[dict[str, Any]]:
        """Get all medication orders for a patient using AQL."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return []

        result = await ehrbase_client.execute_aql(
            MEDICATIONS_QUERY,
            parameters={"ehr_id": patient.ehrId}
        )

        return result.get("rows", [])


medication_service = MedicationService()
