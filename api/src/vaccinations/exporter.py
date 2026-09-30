"""Build CH VACD Immunization Administration document Bundles."""

import uuid
from typing import Any

from src.vaccinations.models import VaccinationRecord
from src.vaccinations.parser import (
    SNOMED_SYSTEM,
    SPID_SYSTEM,
    VACD_IMMUNIZATION_PROFILE,
)

LOINC = "http://loinc.org"


def _cc(c: Any) -> dict[str, Any]:
    coding: dict[str, Any] = {"system": c.system, "code": c.code}
    if c.display:
        coding["display"] = c.display
    return {"coding": [coding]}


def _name(full: str) -> list[dict[str, Any]]:
    parts = full.rsplit(" ", 1)
    if len(parts) == 2:
        return [{"family": parts[1], "given": [parts[0]]}]
    return [{"family": full}]


def record_to_bundle(
    rec: VaccinationRecord,
    patient_spid: str | None = None,
    patient_name: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """Serialise one record as a CH VACD document Bundle.

    Placeholder values (unknown lot, unnamed performer) are omitted rather than
    re-invented. Author provenance is restored: author_kind == "patient" makes
    the Patient the Composition author.
    """
    u = lambda: f"urn:uuid:{uuid.uuid4()}"  # noqa: E731
    comp_url, pat_url, imm_url = u(), u(), u()
    patient: dict[str, Any] = {"resourceType": "Patient", "id": str(uuid.uuid4())}
    spid = patient_spid or rec.patient_spid
    if spid:
        patient["identifier"] = [{"system": SPID_SYSTEM, "value": spid}]
    if patient_name:
        patient["name"] = [{"family": patient_name[1], "given": [patient_name[0]]}]

    imm: dict[str, Any] = {
        "resourceType": "Immunization",
        "id": rec.immunization_id or str(uuid.uuid4()),
        "status": rec.status,
        "vaccineCode": _cc(rec.vaccine),
        "patient": {"reference": pat_url},
        "occurrenceDateTime": rec.occurrence,
    }
    if rec.lot_number:
        imm["lotNumber"] = rec.lot_number
    protocol: dict[str, Any] = {
        "targetDisease": [_cc(t) for t in rec.target_diseases]
    }
    if rec.dose_number is not None:
        protocol["doseNumberPositiveInt"] = rec.dose_number
    if rec.target_diseases or rec.dose_number is not None:
        imm["protocolApplied"] = [protocol]

    author_url = pat_url
    extra: list[dict[str, Any]] = []
    if rec.performer_name or rec.organization_name:
        role: dict[str, Any] = {"resourceType": "PractitionerRole", "id": str(uuid.uuid4())}
        role_url = u()
        if rec.organization_name:
            org_url = u()
            extra.append(
                {"fullUrl": org_url, "resource": {
                    "resourceType": "Organization", "id": str(uuid.uuid4()),
                    "name": rec.organization_name}}
            )
            role["organization"] = {"reference": org_url}
        if rec.performer_name:
            prac_url = u()
            extra.append(
                {"fullUrl": prac_url, "resource": {
                    "resourceType": "Practitioner", "id": str(uuid.uuid4()),
                    "name": _name(rec.performer_name)}}
            )
            role["practitioner"] = {"reference": prac_url}
        extra.append({"fullUrl": role_url, "resource": role})
        imm["performer"] = [{"actor": {"reference": role_url}}]
        if rec.author_kind != "patient":
            author_url = role_url

    composition = {
        "resourceType": "Composition",
        "id": str(uuid.uuid4()),
        "status": "final",
        "type": _cc_simple(SNOMED_SYSTEM, "41000179103", "Immunization record"),
        "subject": {"reference": pat_url},
        "date": rec.occurrence,
        "author": [{"reference": author_url}],
        "title": "Immunization administration",
        "section": [
            {
                "code": _cc_simple(LOINC, "11369-6", "History of Immunization note"),
                "entry": [{"reference": imm_url}],
            }
        ],
    }
    entries = [
        {"fullUrl": comp_url, "resource": composition},
        {"fullUrl": pat_url, "resource": patient},
        *extra,
        {"fullUrl": imm_url, "resource": imm},
    ]
    return {
        "resourceType": "Bundle",
        "meta": {"profile": [VACD_IMMUNIZATION_PROFILE]},
        "identifier": {"system": "urn:ietf:rfc:3986", "value": rec.identifier},
        "type": "document",
        "timestamp": rec.occurrence,
        "entry": entries,
    }


def _cc_simple(system: str, code: str, display: str) -> dict[str, Any]:
    return {"coding": [{"system": system, "code": code, "display": display}]}

