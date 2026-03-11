"""Pydantic models for FHIR terminology operations."""

from pydantic import BaseModel, Field


class CodeLookupResult(BaseModel):
    """Result of a CodeSystem/$lookup operation."""

    code: str
    system: str
    display: str
    version: str | None = None
    properties: dict = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of a $validate-code operation."""

    valid: bool
    message: str | None = None
    display: str | None = None


class ValueSetExpansionEntry(BaseModel):
    """A single code in a value set expansion."""

    code: str
    system: str
    display: str


class ValueSetExpansion(BaseModel):
    """Result of a ValueSet/$expand operation."""

    url: str
    total: int
    contains: list[ValueSetExpansionEntry]


class SubsumptionResult(BaseModel):
    """Result of a CodeSystem/$subsumes operation."""

    outcome: str  # equivalent | subsumes | subsumed-by | not-subsumed


class TerminologySearchResult(BaseModel):
    """Result of a terminology search."""

    results: list[ValueSetExpansionEntry]
    total: int
