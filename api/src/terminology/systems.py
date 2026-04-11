"""Mapping between openEHR terminology identifiers and FHIR system URIs."""

# openEHR terminology_id.value → FHIR canonical system URI
OPENEHR_TO_FHIR_SYSTEM: dict[str, str] = {
    "SNOMED-CT": "http://snomed.info/sct",
    "LOINC": "http://loinc.org",
    "ATC": "http://www.whocc.no/atc",
    "ICD10": "http://hl7.org/fhir/sid/icd-10",
    "ICD10-CM": "http://hl7.org/fhir/sid/icd-10-cm",
}

# Internal terminologies that should not be looked up
INTERNAL_TERMINOLOGIES: set[str] = {"openehr", "local"}


def to_fhir_system(openehr_terminology_id: str) -> str | None:
    """Convert an openEHR terminology identifier to a FHIR system URI.

    Returns None for internal terminologies (openehr, local) that should be skipped.
    If the identifier is already a URI (starts with http), return it as-is.
    """
    lower = openehr_terminology_id.lower()
    if lower in INTERNAL_TERMINOLOGIES:
        return None
    if openehr_terminology_id.startswith("http"):
        return openehr_terminology_id
    return OPENEHR_TO_FHIR_SYSTEM.get(openehr_terminology_id)
