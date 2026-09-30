"""Map VaccinationRecord ↔ FLAT composition for the vaccination template.

Model: COMPOSITION (event) → ACTION.medication (ism_transition = completed)
with vaccine product details (CLUSTER.medication), target disease, dose number,
batch, and a provenance item carrying who authored the record.

NOTE: The FLAT ids below follow the intended template layout
"Open CIS - Vaccination Record.v1" and must be checked against its web
template once the .opt is uploaded (see docs/domain/vaccination-ch-vacd-mapping.md).
Parsing back is suffix-based so it tolerates prefix changes.
"""

from typing import Any

from src.vaccinations.models import Coding, VaccinationRecord

VACCINATION_TEMPLATE_ID = "Open CIS - Vaccination Record.v1"
ROOT = "vaccination_record"
ACT = f"{ROOT}/immunisation"

_KEYS = {
    "vaccine": "vaccine",
    "target": "target_disease",
    "dose": "dose_number",
    "lot": "batch_identifier",
    "performer": "performer_name",
    "org": "organisation_name",
    "author_kind": "author_type",
    "author_name": "author_name",
    "identifier": "external_identifier",
    "status": "status",
}


def build_vaccination_flat(
    rec: VaccinationRecord, composer_name: str = "CIS System"
) -> dict[str, Any]:
    flat: dict[str, Any] = {
        f"{ROOT}/context/start_time": rec.occurrence,
        f"{ROOT}/context/setting|code": "238",
        f"{ROOT}/context/setting|value": "other care",
        f"{ROOT}/context/setting|terminology": "openehr",
        f"{ROOT}/category|code": "433",
        f"{ROOT}/category|value": "event",
        f"{ROOT}/category|terminology": "openehr",
        f"{ROOT}/language|code": "de",
        f"{ROOT}/language|terminology": "ISO_639-1",
        f"{ROOT}/territory|code": "CH",
        f"{ROOT}/territory|terminology": "ISO_3166-1",
        f"{ROOT}/composer|name": rec.author_name or composer_name,
        f"{ACT}/time": rec.occurrence,
        f"{ACT}/language|code": "de",
        f"{ACT}/language|terminology": "ISO_639-1",
        f"{ACT}/encoding|code": "UTF-8",
        f"{ACT}/encoding|terminology": "IANA_character-sets",
        f"{ACT}/ism_transition/current_state|code": "532",
        f"{ACT}/ism_transition/current_state|value": "completed",
        f"{ACT}/ism_transition/current_state|terminology": "openehr",
        f"{ACT}/{_KEYS['vaccine']}|code": rec.vaccine.code,
        f"{ACT}/{_KEYS['vaccine']}|value": rec.vaccine.display or rec.vaccine.code,
        f"{ACT}/{_KEYS['vaccine']}|terminology": rec.vaccine.system,
        f"{ACT}/{_KEYS['identifier']}": rec.identifier,
        f"{ACT}/{_KEYS['author_kind']}": rec.author_kind,
        f"{ACT}/{_KEYS['status']}": rec.status,
    }
    for i, td in enumerate(rec.target_diseases):
        p = f"{ACT}/{_KEYS['target']}:{i}"
        flat[f"{p}|code"] = td.code
        flat[f"{p}|value"] = td.display or td.code
        flat[f"{p}|terminology"] = td.system
    optional = {
        "dose": rec.dose_number,
        "lot": rec.lot_number,
        "performer": rec.performer_name,
        "org": rec.organization_name,
        "author_name": rec.author_name,
    }
    for k, v in optional.items():
        if v is not None:
            flat[f"{ACT}/{_KEYS[k]}"] = v
    return flat


def parse_vaccination_flat(flat: dict[str, Any]) -> VaccinationRecord | None:
    """Rebuild a VaccinationRecord from a FLAT composition (suffix matching)."""

    def find(suffix: str) -> Any:
        for k, v in flat.items():
            if k.endswith(f"/{suffix}") and v not in (None, ""):
                return v
        return None

    code = find(f"{_KEYS['vaccine']}|code")
    if code is None:
        return None
    targets: dict[int, dict[str, str]] = {}
    marker = f"{_KEYS['target']}:"
    for k, v in flat.items():
        if marker in k and "|" in k:
            head, attr = k.rsplit("|", 1)
            idx = int(head.rsplit(marker, 1)[1])
            targets.setdefault(idx, {})[attr] = str(v)
    dose = find(_KEYS["dose"])
    return VaccinationRecord(
        identifier=str(find(_KEYS["identifier"]) or ""),
        vaccine=Coding(
            str(find(f"{_KEYS['vaccine']}|terminology") or ""),
            str(code),
            find(f"{_KEYS['vaccine']}|value"),
        ),
        occurrence=str(find("time") or find("start_time") or ""),
        target_diseases=[
            Coding(t.get("terminology", ""), t["code"], t.get("value"))
            for _, t in sorted(targets.items())
            if "code" in t
        ],
        dose_number=int(dose) if dose is not None else None,
        lot_number=find(_KEYS["lot"]),
        performer_name=find(_KEYS["performer"]),
        organization_name=find(_KEYS["org"]),
        author_kind=find(_KEYS["author_kind"]) or "unknown",
        author_name=find(_KEYS["author_name"]),
        status=find(_KEYS["status"]) or "completed",
    )
