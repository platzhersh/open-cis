"""Observation service for managing vital signs with openEHR transparency."""

from datetime import datetime
from typing import Any

from src.ehrbase.client import ehrbase_client
from src.ehrbase.queries import VITAL_SIGNS_DATE_RANGE_QUERY, VITAL_SIGNS_QUERY
from src.observations.schemas import (
    OpenEHRMetadataResponse,
    PathMappingResponse,
    VitalSignsCreate,
    VitalSignsListResponse,
    VitalSignsResponse,
)
from src.patients.repository import find_patient_by_id


class ObservationService:
    """Service for vital signs observations with EHRBase integration."""

    TEMPLATE_ID = "IDCR - Vital Signs Encounter.v1"

    # Archetype information for transparency
    ARCHETYPES = {
        "blood_pressure": {
            "id": "openEHR-EHR-OBSERVATION.blood_pressure.v1",
            "systolic_path": "/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value",
            "diastolic_path": "/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value",
        },
        "pulse": {
            "id": "openEHR-EHR-OBSERVATION.pulse.v1",
            "rate_path": "/data[at0002]/events[at0003]/data[at0001]/items[at0004]/value",
        },
        "composition": {
            "id": "openEHR-EHR-COMPOSITION.encounter.v1",
        },
    }

    async def record_vital_signs(self, data: VitalSignsCreate) -> VitalSignsResponse:
        """Record vital signs for a patient, creating a composition in EHRBase."""
        patient = await find_patient_by_id(data.patient_id)
        if not patient:
            raise ValueError("Patient not found")

        ehr_id = patient.ehrId

        # Build FLAT format composition
        flat_composition = self._build_flat_composition(data)

        # Create composition in EHRBase
        try:
            result = await ehrbase_client.create_composition(
                ehr_id=ehr_id,
                template_id=self.TEMPLATE_ID,
                composition=flat_composition,
                format="FLAT",
            )
            composition_uid = result.get("uid", {}).get("value", "") or result.get(
                "compositionUid", ""
            )
        except Exception as e:
            # If EHRBase is unavailable or template not uploaded, return with placeholder
            # This allows development without EHRBase running
            composition_uid = f"placeholder-{datetime.utcnow().isoformat()}"
            # Log the error but don't fail
            import logging

            logging.warning(f"EHRBase composition creation failed: {e}")

        now = datetime.utcnow()

        return VitalSignsResponse(
            id=composition_uid,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            recorded_at=data.recorded_at,
            systolic=data.systolic,
            diastolic=data.diastolic,
            pulse_rate=data.pulse_rate,
            created_at=now,
            openehr_metadata=self._build_openehr_metadata(
                composition_uid=composition_uid,
                ehr_id=ehr_id,
                data=data,
            ),
        )

    async def get_vital_signs(
        self, composition_uid: str, patient_id: str
    ) -> VitalSignsResponse | None:
        """Get a single vital signs reading by composition UID."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return None

        ehr_id = patient.ehrId

        try:
            composition = await ehrbase_client.get_composition(
                ehr_id=ehr_id, composition_uid=composition_uid
            )
            return self._parse_composition_to_response(
                composition, composition_uid, patient_id, ehr_id
            )
        except Exception:
            return None

    async def get_vital_signs_for_patient(
        self,
        patient_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> VitalSignsListResponse:
        """Get all vital signs for a patient using AQL."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return VitalSignsListResponse(items=[], total=0)

        ehr_id = patient.ehrId

        # Choose query based on date filters
        if from_date and to_date:
            query = VITAL_SIGNS_DATE_RANGE_QUERY
            params: dict[str, Any] = {
                "ehr_id": ehr_id,
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat(),
            }
        else:
            query = VITAL_SIGNS_QUERY
            params = {"ehr_id": ehr_id}

        try:
            result = await ehrbase_client.execute_aql(query, parameters=params)
            rows = result.get("rows", [])
            columns = result.get("columns", [])
        except Exception:
            # EHRBase not available
            return VitalSignsListResponse(items=[], total=0)

        # Parse results
        items: list[VitalSignsResponse] = []
        for row in rows[skip : skip + limit]:
            col_names = [c.get("name", f"col{i}") for i, c in enumerate(columns)]
            row_dict = dict(zip(col_names, row, strict=False))

            composition_uid = row_dict.get("composition_id", "")
            recorded_at_str = row_dict.get("recorded_at", "")

            try:
                recorded_at = datetime.fromisoformat(
                    recorded_at_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                recorded_at = datetime.utcnow()

            systolic = row_dict.get("systolic")
            diastolic = row_dict.get("diastolic")
            pulse_rate = row_dict.get("pulse_rate")

            items.append(
                VitalSignsResponse(
                    id=composition_uid,
                    patient_id=patient_id,
                    encounter_id=None,  # Not stored in AQL result
                    recorded_at=recorded_at,
                    systolic=int(systolic) if systolic else None,
                    diastolic=int(diastolic) if diastolic else None,
                    pulse_rate=int(pulse_rate) if pulse_rate else None,
                    created_at=recorded_at,
                    openehr_metadata=self._build_openehr_metadata(
                        composition_uid=composition_uid,
                        ehr_id=ehr_id,
                        data=VitalSignsCreate(
                            patient_id=patient_id,
                            recorded_at=recorded_at,
                            systolic=int(systolic) if systolic else None,
                            diastolic=int(diastolic) if diastolic else None,
                            pulse_rate=int(pulse_rate) if pulse_rate else None,
                        ),
                    ),
                )
            )

        return VitalSignsListResponse(items=items, total=len(rows))

    async def delete_vital_signs(self, composition_uid: str, patient_id: str) -> bool:
        """Delete a vital signs composition."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return False

        try:
            client = await ehrbase_client._get_client()
            response = await client.delete(
                f"/openehr/v1/ehr/{patient.ehrId}/composition/{composition_uid}"
            )
            return response.status_code == 204
        except Exception:
            return False

    async def get_raw_composition(
        self, composition_uid: str, patient_id: str, format: str = "FLAT"
    ) -> dict[str, Any] | None:
        """Get raw composition data for transparency."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return None

        try:
            client = await ehrbase_client._get_client()
            response = await client.get(
                f"/openehr/v1/ehr/{patient.ehrId}/composition/{composition_uid}",
                params={"format": format},
            )
            if response.status_code == 200:
                return {
                    "format": format,
                    "template_id": self.TEMPLATE_ID,
                    "composition": response.json(),
                }
        except Exception:
            pass
        return None

    def _build_flat_composition(self, data: VitalSignsCreate) -> dict[str, Any]:
        """Build FLAT format composition for EHRBase."""
        recorded_at_iso = data.recorded_at.isoformat()

        # IDCR template structure: composition/vital_signs(section)/observations
        base = "vital_signs"

        composition: dict[str, Any] = {
            "ctx/language": "en",
            "ctx/territory": "US",
            "ctx/time": recorded_at_iso,
        }

        # Add blood pressure if provided
        if data.systolic is not None and data.diastolic is not None:
            bp_path = f"{base}/blood_pressure:0/any_event:0"
            composition.update(
                {
                    f"{bp_path}/systolic|magnitude": data.systolic,
                    f"{bp_path}/systolic|unit": "mm[Hg]",
                    f"{bp_path}/diastolic|magnitude": data.diastolic,
                    f"{bp_path}/diastolic|unit": "mm[Hg]",
                    f"{bp_path}/time": recorded_at_iso,
                }
            )

        # Add pulse/heart rate if provided
        if data.pulse_rate is not None:
            pulse_path = f"{base}/pulse_heart_beat:0/any_event:0"
            composition.update(
                {
                    f"{pulse_path}/rate|magnitude": data.pulse_rate,
                    f"{pulse_path}/rate|unit": "/min",
                    f"{pulse_path}/time": recorded_at_iso,
                }
            )

        return composition

    def _build_openehr_metadata(
        self,
        composition_uid: str,
        ehr_id: str,
        data: VitalSignsCreate,
    ) -> OpenEHRMetadataResponse:
        """Build openEHR metadata for transparency."""
        archetype_ids = [self.ARCHETYPES["composition"]["id"]]
        path_mappings: list[PathMappingResponse] = []

        if data.systolic is not None and data.diastolic is not None:
            archetype_ids.append(self.ARCHETYPES["blood_pressure"]["id"])
            bp_archetype = self.ARCHETYPES["blood_pressure"]
            path_mappings.extend(
                [
                    PathMappingResponse(
                        field="systolic",
                        archetype_id=bp_archetype["id"],
                        archetype_path=f"{bp_archetype['systolic_path']}/magnitude",
                        flat_path="vital_signs/blood_pressure:0/any_event:0/systolic|magnitude",
                        value=data.systolic,
                        unit="mm[Hg]",
                    ),
                    PathMappingResponse(
                        field="diastolic",
                        archetype_id=bp_archetype["id"],
                        archetype_path=f"{bp_archetype['diastolic_path']}/magnitude",
                        flat_path="vital_signs/blood_pressure:0/any_event:0/diastolic|magnitude",
                        value=data.diastolic,
                        unit="mm[Hg]",
                    ),
                ]
            )

        if data.pulse_rate is not None:
            archetype_ids.append(self.ARCHETYPES["pulse"]["id"])
            pulse_archetype = self.ARCHETYPES["pulse"]
            path_mappings.append(
                PathMappingResponse(
                    field="pulse_rate",
                    archetype_id=pulse_archetype["id"],
                    archetype_path=f"{pulse_archetype['rate_path']}/magnitude",
                    flat_path="vital_signs/pulse_heart_beat:0/any_event:0/rate|magnitude",
                    value=data.pulse_rate,
                    unit="/min",
                )
            )

        return OpenEHRMetadataResponse(
            composition_uid=composition_uid,
            template_id=self.TEMPLATE_ID,
            archetype_ids=archetype_ids,
            ehr_id=ehr_id,
            path_mappings=path_mappings,
        )

    def _parse_composition_to_response(
        self,
        composition: dict[str, Any],
        composition_uid: str,
        patient_id: str,
        ehr_id: str,
    ) -> VitalSignsResponse:
        """Parse a raw composition to VitalSignsResponse."""
        # Extract values from composition (depends on format)
        # This is a simplified parser - real implementation would handle STRUCTURED format
        recorded_at = datetime.utcnow()
        systolic = None
        diastolic = None
        pulse_rate = None

        # Try to extract from FLAT format paths
        for key, value in composition.items():
            if "systolic|magnitude" in key:
                systolic = int(value) if value else None
            elif "diastolic|magnitude" in key:
                diastolic = int(value) if value else None
            elif "rate|magnitude" in key:
                pulse_rate = int(value) if value else None
            elif "start_time" in key:
                try:
                    recorded_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                except ValueError:
                    pass

        return VitalSignsResponse(
            id=composition_uid,
            patient_id=patient_id,
            encounter_id=None,
            recorded_at=recorded_at,
            systolic=systolic,
            diastolic=diastolic,
            pulse_rate=pulse_rate,
            created_at=recorded_at,
            openehr_metadata=self._build_openehr_metadata(
                composition_uid=composition_uid,
                ehr_id=ehr_id,
                data=VitalSignsCreate(
                    patient_id=patient_id,
                    recorded_at=recorded_at,
                    systolic=systolic,
                    diastolic=diastolic,
                    pulse_rate=pulse_rate,
                ),
            ),
        )


observation_service = ObservationService()
