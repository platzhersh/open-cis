"""Parse CH VACD FHIR document Bundles into VaccinationRecord objects."""

from typing import Any

from src.vaccinations.models import AuthorKind, Coding, VaccinationRecord, clean

SWISSMEDIC_SYSTEM = "http://fhir.ch/ig/ch-vacd/CodeSystem/ch-vacd-swissmedic-cs"
SNOMED_SYSTEM = "http://snomed.info/sct"
SPID_SYSTEM = "urn:oid:2.16.756.5.30.1.127.3.10.3"
VACD_IMMUNIZATION_PROFILE = (
    "http://fhir.ch/ig/ch-vacd/StructureDefinition/"
    "ch-vacd-document-immunization-administration"
)


class VacdParseError(ValueError):
    """Raised when a Bundle is not a usable CH VACD immunization document."""


def _by_type(bundle: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for entry in bundle.get("entry", []):
        res = entry.get("resource") or {}
        out.setdefault(res.get("resourceType", ""), []).append(res)
    return out


def _resolve(bundle: dict[str, Any], reference: str | None) -> dict[str, Any] | None:
    """Resolve a reference (fullUrl or Type/id) within the Bundle."""
    if not reference:
        return None
    for entry in bundle.get("entry", []):
        res = entry.get("resource") or {}
        if entry.get("fullUrl") == reference or (
            f"{res.get('resourceType')}/{res.get('id')}" == reference
        ):
            return res
    return None


def _human_name(resource: dict[str, Any] | None) -> str | None:
    if not resource:
        return None
    if resource.get("resourceType") == "Organization":
        return clean(resource.get("name"))
    names = resource.get("name") or []
    if not names:
        return None
    n = names[0]
    parts = [*n.get("given", []), n.get("family", "")]
    return clean(" ".join(p for p in parts if clean(p)))


def _coding(cc: dict[str, Any] | None, system: str | None = None) -> Coding | None:
    for c in (cc or {}).get("coding", []):
        if c.get("code") and (system is None or c.get("system") == system):
            return Coding(c.get("system", ""), c["code"], c.get("display"))
    return None


def _author(bundle: dict[str, Any], composition: dict[str, Any] | None) -> tuple[
    AuthorKind, str | None
]:
    if not composition:
        return "unknown", None
    for ref in composition.get("author", []):
        res = _resolve(bundle, ref.get("reference"))
        rtype = (res or {}).get("resourceType")
        if rtype == "Patient":
            return "patient", _human_name(res)
        if rtype in ("Practitioner", "PractitionerRole"):
            if res is not None and rtype == "PractitionerRole":
                res = _resolve(bundle, res.get("practitioner", {}).get("reference"))
            return "practitioner", _human_name(res)
        if rtype == "Device":
            return "device", None
    return "unknown", None


def parse_bundle(bundle: dict[str, Any]) -> VaccinationRecord:
    """Parse one CH VACD Immunization Administration document Bundle."""
    if bundle.get("resourceType") != "Bundle":
        raise VacdParseError("Not a FHIR Bundle")
    by_type = _by_type(bundle)
    immunizations = by_type.get("Immunization", [])
    if len(immunizations) != 1:
        raise VacdParseError(
            f"Expected exactly 1 Immunization, found {len(immunizations)}"
        )
    imm = immunizations[0]

    vaccine = _coding(imm.get("vaccineCode"), SWISSMEDIC_SYSTEM) or _coding(
        imm.get("vaccineCode")
    )
    if vaccine is None:
        raise VacdParseError("Immunization.vaccineCode has no coding")
    occurrence = imm.get("occurrenceDateTime") or imm.get("occurrenceString")
    if not occurrence:
        raise VacdParseError("Immunization.occurrence[x] is missing")

    targets: list[Coding] = []
    dose_number: int | None = None
    for proto in imm.get("protocolApplied", []):
        for td in proto.get("targetDisease", []):
            c = _coding(td, SNOMED_SYSTEM) or _coding(td)
            if c and c not in targets:
                targets.append(c)
        if dose_number is None and "doseNumberPositiveInt" in proto:
            dose_number = int(proto["doseNumberPositiveInt"])

    performer_name = organization_name = None
    for perf in imm.get("performer", []):
        actor = _resolve(bundle, (perf.get("actor") or {}).get("reference"))
        if actor and actor.get("resourceType") == "PractitionerRole":
            organization_name = organization_name or _human_name(
                _resolve(bundle, actor.get("organization", {}).get("reference"))
            )
            practitioner = _resolve(
                bundle, actor.get("practitioner", {}).get("reference")
            )
            performer_name = performer_name or _human_name(practitioner)
        elif actor and actor.get("resourceType") == "Practitioner":
            performer_name = performer_name or _human_name(actor)
        elif actor and actor.get("resourceType") == "Organization":
            organization_name = organization_name or _human_name(actor)

    compositions = by_type.get("Composition")
    composition = compositions[0] if compositions else None
    author_kind, author_name = _author(bundle, composition)

    spid = None
    for patient in by_type.get("Patient", []):
        for ident in patient.get("identifier", []):
            if ident.get("system") == SPID_SYSTEM:
                spid = ident.get("value")

    bundle_ident = (bundle.get("identifier") or {}).get("value")
    identifier = bundle_ident or imm.get("id")
    if not identifier:
        raise VacdParseError("Neither Bundle.identifier nor Immunization.id present")

    return VaccinationRecord(
        identifier=str(identifier),
        vaccine=vaccine,
        occurrence=occurrence,
        target_diseases=targets,
        dose_number=dose_number,
        lot_number=clean(imm.get("lotNumber")),
        performer_name=performer_name,
        organization_name=organization_name,
        author_kind=author_kind,
        author_name=author_name,
        status=imm.get("status", "completed"),
        patient_spid=spid,
        immunization_id=imm.get("id"),
    )
