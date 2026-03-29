"""CAVE service for managing allergies & adverse reactions with openEHR."""

import logging
from datetime import UTC, datetime
from typing import Any

from src.cave.schemas import (
    CaveCategory,
    CaveCriticality,
    CaveEntryCreate,
    CaveEntryResponse,
    CaveEntryUpdate,
    CaveListResponse,
    CaveReactionType,
    CaveStatus,
    CaveSummaryResponse,
    NkaRequest,
    NkaResponse,
    ReactionCertainty,
    ReactionEvent,
    ReactionSeverity,
)
from src.ehrbase.client import ehrbase_client
from src.ehrbase.queries import CAVE_ENTRIES_QUERY, NKA_CHECK_QUERY
from src.errors import PatientNotFoundError
from src.openehr.compositions import (
    ADVERSE_REACTION_TEMPLATE_ID,
    build_adverse_reaction_flat,
    build_nka_flat,
)
from src.openehr.path_resolver import resolve_adverse_reaction_paths
from src.patients.repository import find_patient_by_id

logger = logging.getLogger(__name__)


class CaveService:
    """Service for CAVE (allergies/adverse reactions) with EHRBase integration."""

    TEMPLATE_ID = ADVERSE_REACTION_TEMPLATE_ID

    ARCHETYPES = {
        "adverse_reaction": {
            "id": "openEHR-EHR-EVALUATION.adverse_reaction_risk.v1",
        },
        "exclusion_global": {
            "id": "openEHR-EHR-EVALUATION.exclusion_global.v1",
        },
    }

    async def create_cave_entry(self, data: CaveEntryCreate) -> CaveEntryResponse:
        """Create a new CAVE entry as a composition in EHRBase.

        Raises:
            PatientNotFoundError: If the patient does not exist.
            EHRBaseValidationError: If EHRBase rejects the composition.
            EHRBaseUnavailableError: If EHRBase is not reachable.
        """
        patient = await find_patient_by_id(data.patient_id)
        if not patient:
            raise PatientNotFoundError(message=f"Patient {data.patient_id} not found")

        ehr_id = patient.ehrId

        # Resolve correct FLAT path IDs from the web template
        resolved_paths = await resolve_adverse_reaction_paths(self.TEMPLATE_ID)

        flat_composition = build_adverse_reaction_flat(
            substance=data.substance,
            category=data.category.value,
            reaction_type=data.reaction_type.value,
            criticality=data.criticality.value,
            status=data.status.value,
            onset_date=data.onset_date,
            comment=data.comment,
            reactions=[
                {
                    "manifestation": r.manifestation,
                    "severity": r.severity.value,
                    "certainty": r.certainty.value,
                    "onset_date": r.onset_date,
                    "description": r.description,
                }
                for r in data.reactions
            ],
            resolved_paths=resolved_paths,
        )

        result = await ehrbase_client.create_composition(
            ehr_id=ehr_id,
            template_id=self.TEMPLATE_ID,
            composition=flat_composition,
            format="FLAT",
        )
        composition_uid = result.get("uid", {}).get("value", "") or result.get(
            "compositionUid", ""
        )

        now = datetime.now(UTC)

        return CaveEntryResponse(
            id=composition_uid,
            ehr_id=ehr_id,
            patient_id=data.patient_id,
            substance=data.substance,
            category=data.category,
            reaction_type=data.reaction_type,
            criticality=data.criticality,
            status=data.status,
            onset_date=data.onset_date,
            recorded_date=now,
            last_updated=now,
            comment=data.comment,
            reactions=data.reactions,
            composition_uid=composition_uid,
            template_id=self.TEMPLATE_ID,
            archetype_ids=[self.ARCHETYPES["adverse_reaction"]["id"]],
        )

    async def get_cave_entries(
        self,
        patient_id: str,
        status: str | None = None,
        category: str | None = None,
    ) -> CaveListResponse:
        """Get all CAVE entries for a patient using AQL."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return CaveListResponse(items=[], total=0)

        ehr_id = patient.ehrId

        result = await ehrbase_client.execute_aql(
            CAVE_ENTRIES_QUERY, parameters={"ehr_id": ehr_id}
        )
        rows = result.get("rows", [])
        columns = result.get("columns", [])

        items: list[CaveEntryResponse] = []
        for row in rows:
            col_names = [c.get("name", f"col{i}") for i, c in enumerate(columns)]
            row_dict = dict(zip(col_names, row, strict=False))

            entry = self._parse_aql_row(row_dict, patient_id, ehr_id)
            if entry is None:
                continue

            # Apply filters
            if status and entry.status.value != status:
                continue
            if category and entry.category.value != category:
                continue

            items.append(entry)

        return CaveListResponse(items=items, total=len(items))

    async def get_cave_entry(
        self, composition_uid: str, patient_id: str
    ) -> CaveEntryResponse | None:
        """Get a single CAVE entry by composition UID.

        Raises:
            EHRBaseUnavailableError: If EHRBase is not reachable.
        """
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return None

        composition = await ehrbase_client.get_composition(
            ehr_id=patient.ehrId, composition_uid=composition_uid
        )
        return self._parse_composition_to_response(
            composition, composition_uid, patient_id, patient.ehrId
        )

    async def update_cave_entry(
        self,
        composition_uid: str,
        patient_id: str,
        data: CaveEntryUpdate,
    ) -> CaveEntryResponse | None:
        """Update a CAVE entry by deleting and recreating the composition."""
        existing = await self.get_cave_entry(composition_uid, patient_id)
        if not existing:
            return None

        # Build updated entry
        updated_criticality = data.criticality or existing.criticality
        updated_status = data.status or existing.status
        updated_comment = data.comment if data.comment is not None else existing.comment
        updated_reactions = (
            data.reactions if data.reactions is not None else existing.reactions
        )

        # Delete old composition
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return None

        await ehrbase_client.delete_composition(patient.ehrId, composition_uid)

        # Create new composition with updated data
        create_data = CaveEntryCreate(
            patient_id=patient_id,
            substance=existing.substance,
            category=existing.category,
            reaction_type=existing.reaction_type,
            criticality=updated_criticality,
            status=updated_status,
            onset_date=existing.onset_date,
            comment=updated_comment,
            reactions=updated_reactions,
        )

        return await self.create_cave_entry(create_data)

    async def delete_cave_entry(
        self, composition_uid: str, patient_id: str
    ) -> bool:
        """Delete a CAVE entry composition.

        Raises:
            PatientNotFoundError: If the patient does not exist.
            EHRBaseUnavailableError: If EHRBase is not reachable.
        """
        patient = await find_patient_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(message=f"Patient {patient_id} not found")

        return await ehrbase_client.delete_composition(
            patient.ehrId, composition_uid
        )

    async def get_cave_summary(self, patient_id: str) -> CaveSummaryResponse:
        """Get CAVE summary for the patient banner."""
        patient = await find_patient_by_id(patient_id)
        if not patient:
            return CaveSummaryResponse(
                patient_id=patient_id,
                total_active=0,
                has_high_criticality=False,
                has_nka_declaration=False,
                entries=[],
            )

        entries_response = await self.get_cave_entries(patient_id)
        entries = entries_response.items

        active_entries = [e for e in entries if e.status == CaveStatus.ACTIVE]
        has_high = any(
            e.criticality == CaveCriticality.HIGH for e in active_entries
        )

        # Check for NKA declaration via dedicated AQL query for exclusion_global archetype
        nka_result = await ehrbase_client.execute_aql(
            NKA_CHECK_QUERY, parameters={"ehr_id": patient.ehrId}
        )
        has_nka = bool(nka_result.get("rows"))

        return CaveSummaryResponse(
            patient_id=patient_id,
            total_active=len(active_entries),
            has_high_criticality=has_high,
            has_nka_declaration=has_nka,
            entries=active_entries,
        )

    async def remove_nka(self, patient_id: str) -> bool:
        """Remove 'No Known Allergies' declaration by deleting the NKA composition.

        Raises:
            PatientNotFoundError: If the patient does not exist.
        """
        patient = await find_patient_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(message=f"Patient {patient_id} not found")

        ehr_id = patient.ehrId

        nka_result = await ehrbase_client.execute_aql(
            NKA_CHECK_QUERY, parameters={"ehr_id": ehr_id}
        )
        rows = nka_result.get("rows", [])
        if not rows:
            return False

        composition_uid = rows[0][0]
        return await ehrbase_client.delete_composition(ehr_id, composition_uid)

    async def record_nka(self, data: NkaRequest) -> NkaResponse:
        """Record 'No Known Allergies' for a patient.

        Raises:
            PatientNotFoundError: If the patient does not exist.
            EHRBaseValidationError: If EHRBase rejects the composition.
            EHRBaseUnavailableError: If EHRBase is not reachable.
        """
        patient = await find_patient_by_id(data.patient_id)
        if not patient:
            raise PatientNotFoundError(message=f"Patient {data.patient_id} not found")

        ehr_id = patient.ehrId

        # Resolve correct FLAT path IDs from the web template
        resolved_paths = await resolve_adverse_reaction_paths(self.TEMPLATE_ID)

        flat_composition = build_nka_flat(resolved_paths=resolved_paths)

        result = await ehrbase_client.create_composition(
            ehr_id=ehr_id,
            template_id=self.TEMPLATE_ID,
            composition=flat_composition,
            format="FLAT",
        )
        composition_uid = result.get("uid", {}).get("value", "") or result.get(
            "compositionUid", ""
        )

        return NkaResponse(
            patient_id=data.patient_id,
            has_nka_declaration=True,
            composition_uid=composition_uid,
        )

    def _parse_aql_row(
        self,
        row_dict: dict[str, Any],
        patient_id: str,
        ehr_id: str,
    ) -> CaveEntryResponse | None:
        """Parse an AQL result row to CaveEntryResponse."""
        composition_uid = row_dict.get("composition_uid", "")
        substance = row_dict.get("substance")
        if not substance:
            return None

        # Parse category
        category_raw = row_dict.get("category", "other")
        try:
            category = CaveCategory(category_raw) if category_raw else CaveCategory.OTHER
        except ValueError:
            category = CaveCategory.OTHER

        # Parse criticality
        criticality_raw = row_dict.get("criticality", "indeterminate")
        try:
            criticality = (
                CaveCriticality(criticality_raw)
                if criticality_raw
                else CaveCriticality.INDETERMINATE
            )
        except ValueError:
            criticality = CaveCriticality.INDETERMINATE

        # Parse status
        status_raw = row_dict.get("status", "active")
        try:
            status = CaveStatus(status_raw) if status_raw else CaveStatus.ACTIVE
        except ValueError:
            status = CaveStatus.ACTIVE

        # Parse reaction type
        reaction_type_raw = row_dict.get("reaction_type", "unknown")
        try:
            reaction_type = (
                CaveReactionType(reaction_type_raw)
                if reaction_type_raw
                else CaveReactionType.UNKNOWN
            )
        except ValueError:
            reaction_type = CaveReactionType.UNKNOWN

        # Parse dates
        recorded_at_str = row_dict.get("recorded_at", "")
        try:
            recorded_date = datetime.fromisoformat(
                recorded_at_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            recorded_date = datetime.now(UTC)

        comment = row_dict.get("comment")

        # Parse onset date
        onset_raw = row_dict.get("onset_of_last_reaction")
        onset_date = None
        if onset_raw:
            try:
                onset_date = datetime.fromisoformat(
                    str(onset_raw).replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        # Parse reaction events from AQL results
        manifestation = row_dict.get("manifestation")
        severity_raw = row_dict.get("severity")
        certainty_raw = row_dict.get("certainty")
        reaction_onset_raw = row_dict.get("onset_of_reaction")
        reaction_description = row_dict.get("reaction_description")

        reactions: list[ReactionEvent] = []
        if manifestation:
            try:
                severity = (
                    ReactionSeverity(severity_raw)
                    if severity_raw
                    else ReactionSeverity.MODERATE
                )
            except ValueError:
                severity = ReactionSeverity.MODERATE

            try:
                certainty = (
                    ReactionCertainty(certainty_raw)
                    if certainty_raw
                    else ReactionCertainty.SUSPECTED
                )
            except ValueError:
                certainty = ReactionCertainty.SUSPECTED

            reaction_onset = None
            if reaction_onset_raw:
                try:
                    reaction_onset = datetime.fromisoformat(
                        str(reaction_onset_raw).replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

            reactions.append(
                ReactionEvent(
                    manifestation=str(manifestation),
                    severity=severity,
                    certainty=certainty,
                    onset_date=reaction_onset,
                    description=(
                        str(reaction_description) if reaction_description else None
                    ),
                )
            )

        return CaveEntryResponse(
            id=composition_uid,
            ehr_id=ehr_id,
            patient_id=patient_id,
            substance=str(substance),
            category=category,
            reaction_type=reaction_type,
            criticality=criticality,
            status=status,
            onset_date=onset_date,
            recorded_date=recorded_date,
            last_updated=recorded_date,
            comment=str(comment) if comment else None,
            reactions=reactions,
            composition_uid=composition_uid,
            template_id=self.TEMPLATE_ID,
            archetype_ids=[self.ARCHETYPES["adverse_reaction"]["id"]],
        )

    def _parse_composition_to_response(
        self,
        composition: dict[str, Any],
        composition_uid: str,
        patient_id: str,
        ehr_id: str,
    ) -> CaveEntryResponse:
        """Parse a raw composition to CaveEntryResponse."""
        substance = ""
        category = CaveCategory.OTHER
        reaction_type = CaveReactionType.UNKNOWN
        criticality = CaveCriticality.INDETERMINATE
        status = CaveStatus.ACTIVE
        comment = None
        reactions: list[ReactionEvent] = []
        recorded_date = datetime.now(UTC)

        for key, value in composition.items():
            if ("substance" in key or "causative_agent" in key) and value:
                substance = str(value)
            elif "category" in key and "|code" in key and value:
                try:
                    category = CaveCategory(str(value))
                except ValueError:
                    pass
            elif "reaction_type" in key and "|code" in key and value:
                try:
                    reaction_type = CaveReactionType(str(value))
                except ValueError:
                    pass
            elif "criticality" in key and "|code" in key and value:
                try:
                    criticality = CaveCriticality(str(value))
                except ValueError:
                    pass
            elif "status" in key and "|code" in key and value:
                try:
                    status = CaveStatus(str(value))
                except ValueError:
                    pass
            elif "comment" in key and value:
                comment = str(value)
            elif "start_time" in key and value:
                try:
                    recorded_date = datetime.fromisoformat(
                        str(value).replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

        return CaveEntryResponse(
            id=composition_uid,
            ehr_id=ehr_id,
            patient_id=patient_id,
            substance=substance,
            category=category,
            reaction_type=reaction_type,
            criticality=criticality,
            status=status,
            onset_date=None,
            recorded_date=recorded_date,
            last_updated=recorded_date,
            comment=comment,
            reactions=reactions,
            composition_uid=composition_uid,
            template_id=self.TEMPLATE_ID,
            archetype_ids=[self.ARCHETYPES["adverse_reaction"]["id"]],
        )


cave_service = CaveService()
