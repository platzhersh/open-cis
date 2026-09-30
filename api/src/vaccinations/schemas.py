"""API schemas for vaccination records."""

from pydantic import BaseModel


class CodingOut(BaseModel):
    system: str
    code: str
    display: str | None = None


class VaccinationOut(BaseModel):
    composition_uid: str
    identifier: str
    vaccine: CodingOut
    occurrence: str
    target_diseases: list[CodingOut]
    dose_number: int | None
    lot_number: str | None
    performer_name: str | None
    organization_name: str | None
    author_kind: str
    author_name: str | None
    probable_duplicate: bool = False
    duplicate_of: list[str] = []


class VaccinationListResponse(BaseModel):
    items: list[VaccinationOut]
    total: int
    duplicate_groups: list[list[str]]  # composition UIDs per duplicate group


class ImportItemResult(BaseModel):
    identifier: str
    status: str  # created | skipped_existing | error
    composition_uid: str | None = None
    error: str | None = None


class ImportResponse(BaseModel):
    created: int
    skipped_existing: int
    errors: int
    skipped_documents: list[str]
    results: list[ImportItemResult]
