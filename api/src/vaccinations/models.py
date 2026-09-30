"""Domain model for a single vaccination administration (CH VACD ↔ openEHR)."""

from dataclasses import dataclass, field
from typing import Literal

AuthorKind = Literal["patient", "practitioner", "device", "unknown"]

# Placeholder values seen in real EPD exports that mean "unknown".
PLACEHOLDERS = frozenset({"", "-", "?", "--", "n/a", "unknown"})


def clean(value: str | None) -> str | None:
    """Return None for empty/placeholder strings, else the stripped value."""
    if value is None:
        return None
    stripped = value.strip()
    return None if stripped.lower() in PLACEHOLDERS else stripped


@dataclass(frozen=True)
class Coding:
    system: str
    code: str
    display: str | None = None


@dataclass
class VaccinationRecord:
    """One administered vaccine dose, independent of FHIR/openEHR syntax."""

    identifier: str  # idempotency key (Bundle identifier, else Immunization.id)
    vaccine: Coding
    occurrence: str  # ISO 8601 date or dateTime, kept verbatim
    target_diseases: list[Coding] = field(default_factory=list)
    dose_number: int | None = None
    lot_number: str | None = None
    performer_name: str | None = None
    organization_name: str | None = None
    author_kind: AuthorKind = "unknown"
    author_name: str | None = None
    status: str = "completed"
    patient_spid: str | None = None
    # FHIR ids, kept so the export can keep stable references
    immunization_id: str | None = None

    @property
    def occurrence_date(self) -> str:
        return self.occurrence[:10]

    @property
    def duplicate_key(self) -> tuple[str, str]:
        return (self.vaccine.code, self.occurrence_date)
