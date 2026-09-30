"""Vaccination service: CH VACD (FHIR) ↔ openEHR via EHRBase."""

import json
import logging
from typing import Any

from src.ehrbase.client import ehrbase_client
from src.ehrbase.queries import VACCINATIONS_QUERY
from src.errors import OpenCISError, PatientNotFoundError
from src.patients.repository import find_patient_by_id
from src.vaccinations.duplicates import find_duplicate_groups
from src.vaccinations.exporter import record_to_bundle
from src.vaccinations.flat import (
    VACCINATION_TEMPLATE_ID,
    build_vaccination_flat,
    parse_vaccination_flat,
)
from src.vaccinations.models import Coding, VaccinationRecord
from src.vaccinations.parser import VacdParseError, parse_bundle
from src.vaccinations.schemas import (
    CodingOut,
    ImportItemResult,
    ImportResponse,
    VaccinationListResponse,
    VaccinationOut,
)
from src.vaccinations.xdm import read_xdm_zip

logger = logging.getLogger(__name__)


def _coding_out(c: Coding) -> CodingOut:
    return CodingOut(system=c.system, code=c.code, display=c.display)


class VaccinationService:
    async def _ehr_id(self, patient_id: str) -> str:
        patient = await find_patient_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(message=f"Patient {patient_id} not found")
        return str(patient.ehrId)

    async def _load(self, ehr_id: str) -> list[tuple[str, VaccinationRecord]]:
        result = await ehrbase_client.execute_aql(
            VACCINATIONS_QUERY, parameters={"ehr_id": ehr_id}
        )
        out: list[tuple[str, VaccinationRecord]] = []
        for row in result.get("rows", []):
            uid = row[0]
            flat = await ehrbase_client.get_composition_formatted(ehr_id, uid, "FLAT")
            rec = parse_vaccination_flat(flat)
            if rec:
                out.append((uid, rec))
        return out

    async def import_payload(
        self, patient_id: str, content: bytes, is_zip: bool
    ) -> ImportResponse:
        ehr_id = await self._ehr_id(patient_id)
        skipped_docs: list[str] = []
        if is_zip:
            xdm = read_xdm_zip(content)
            bundles, skipped_docs = xdm.bundles, xdm.skipped
        else:
            parsed = json.loads(content)
            bundles = [parsed]

        existing = {r.identifier for _, r in await self._load(ehr_id)}
        results: list[ImportItemResult] = []
        for bundle in bundles:
            ident = str((bundle.get("identifier") or {}).get("value", "?"))
            try:
                rec = parse_bundle(bundle)
                ident = rec.identifier
                if rec.identifier in existing:
                    results.append(ImportItemResult(identifier=ident, status="skipped_existing"))
                    continue
                created = await ehrbase_client.create_composition(
                    ehr_id=ehr_id,
                    template_id=VACCINATION_TEMPLATE_ID,
                    composition=build_vaccination_flat(rec),
                    format="FLAT",
                )
                existing.add(rec.identifier)
                results.append(
                    ImportItemResult(
                        identifier=ident,
                        status="created",
                        composition_uid=created.get("compositionUid"),
                    )
                )
            except (VacdParseError, OpenCISError) as e:
                logger.warning("Vaccination import failed for %s: %s", ident, e)
                results.append(ImportItemResult(identifier=ident, status="error", error=str(e)))

        def count(s: str) -> int:
            return sum(1 for r in results if r.status == s)

        return ImportResponse(
            created=count("created"),
            skipped_existing=count("skipped_existing"),
            errors=count("error"),
            skipped_documents=skipped_docs,
            results=results,
        )

    async def list_vaccinations(self, patient_id: str) -> VaccinationListResponse:
        ehr_id = await self._ehr_id(patient_id)
        loaded = await self._load(ehr_id)
        uid_by_id = {id(r): uid for uid, r in loaded}
        groups = find_duplicate_groups([r for _, r in loaded])
        dup_uids: dict[str, list[str]] = {}
        for g in groups:
            uids = [uid_by_id[id(r)] for r in g]
            for u in uids:
                dup_uids[u] = [x for x in uids if x != u]
        items = [
            VaccinationOut(
                composition_uid=uid,
                identifier=r.identifier,
                vaccine=_coding_out(r.vaccine),
                occurrence=r.occurrence,
                target_diseases=[_coding_out(t) for t in r.target_diseases],
                dose_number=r.dose_number,
                lot_number=r.lot_number,
                performer_name=r.performer_name,
                organization_name=r.organization_name,
                author_kind=r.author_kind,
                author_name=r.author_name,
                probable_duplicate=uid in dup_uids,
                duplicate_of=dup_uids.get(uid, []),
            )
            for uid, r in loaded
        ]
        return VaccinationListResponse(
            items=items,
            total=len(items),
            duplicate_groups=[[uid_by_id[id(r)] for r in g] for g in groups],
        )

    async def export_bundles(self, patient_id: str) -> list[dict[str, Any]]:
        ehr_id = await self._ehr_id(patient_id)
        patient = await find_patient_by_id(patient_id)
        name = (patient.givenName, patient.familyName) if patient else None
        return [record_to_bundle(r, patient_name=name) for _, r in await self._load(ehr_id)]


vaccination_service = VaccinationService()
