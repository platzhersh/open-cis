"""Schemas for CAVE (allergies & adverse reactions) with openEHR transparency."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CaveCategory(StrEnum):
    MEDICATION = "medication"
    FOOD = "food"
    ENVIRONMENT = "environment"
    OTHER = "other"


class CaveReactionType(StrEnum):
    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"
    UNKNOWN = "unknown"


class CaveCriticality(StrEnum):
    LOW = "low"
    HIGH = "high"
    INDETERMINATE = "indeterminate"


class CaveStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    REFUTED = "refuted"


class ReactionSeverity(StrEnum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ReactionCertainty(StrEnum):
    SUSPECTED = "suspected"
    LIKELY = "likely"
    CONFIRMED = "confirmed"


class ReactionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifestation: str = Field(..., min_length=1, max_length=200)
    severity: ReactionSeverity
    certainty: ReactionCertainty
    onset_date: datetime | None = None
    description: str | None = Field(None, max_length=500)


class CaveEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str
    substance: str = Field(..., min_length=1, max_length=200)
    category: CaveCategory
    reaction_type: CaveReactionType
    criticality: CaveCriticality
    status: CaveStatus = CaveStatus.ACTIVE
    onset_date: datetime | None = None
    comment: str | None = Field(None, max_length=1000)
    reactions: list[ReactionEvent] = Field(default_factory=list)


class CaveEntryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criticality: CaveCriticality | None = None
    status: CaveStatus | None = None
    comment: str | None = Field(None, max_length=1000)
    reactions: list[ReactionEvent] | None = None


class CaveEntryResponse(BaseModel):
    id: str
    ehr_id: str
    patient_id: str
    substance: str
    category: CaveCategory
    reaction_type: CaveReactionType
    criticality: CaveCriticality
    status: CaveStatus
    onset_date: datetime | None
    recorded_date: datetime
    last_updated: datetime
    comment: str | None
    reactions: list[ReactionEvent]
    composition_uid: str
    template_id: str
    archetype_ids: list[str]


class CaveListResponse(BaseModel):
    items: list[CaveEntryResponse]
    total: int


class CaveSummaryResponse(BaseModel):
    patient_id: str
    total_active: int
    has_high_criticality: bool
    has_nka_declaration: bool
    entries: list[CaveEntryResponse]


class NkaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str


class NkaResponse(BaseModel):
    patient_id: str
    has_nka_declaration: bool
    composition_uid: str
