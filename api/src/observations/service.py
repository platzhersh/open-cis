"""Observation service for managing vital signs and measurements."""

from datetime import datetime
from typing import Any

from src.ehrbase.client import ehrbase_client
from src.ehrbase.queries import VITAL_SIGNS_QUERY
from src.patients.repository import find_patient_by_id
from src.observations.schemas import VitalSignsCreate, VitalSignsResponse


class ObservationService:
    async def record_vital_signs(self, data: VitalSignsCreate) -> VitalSignsResponse:
        """Record vital signs for a patient."""
        patient = await find_patient_by_id(data.patient_id)
        if not patient:
            raise ValueError("Patient not found")

        recorded_at = data.recorded_at or datetime.utcnow()

        # For now, return a placeholder - composition creation requires templates
        return VitalSignsResponse(
            composition_uid=None,
            patient_id=data.patient_id,
            systolic_bp=data.systolic_bp,
            diastolic_bp=data.diastolic_bp,
            heart_rate=data.heart_rate,
            temperature=data.temperature,
            respiratory_rate=data.respiratory_rate,
            oxygen_saturation=data.oxygen_saturation,
            recorded_at=recorded_at,
        )

    async def get_vital_signs_for_patient(self, patient_id: str) -> list[dict[str, Any]]:
        """Get all vital signs for a patient using AQL."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return []

        result = await ehrbase_client.execute_aql(
            VITAL_SIGNS_QUERY,
            parameters={"ehr_id": patient.ehrId}
        )

        return result.get("rows", [])


observation_service = ObservationService()
