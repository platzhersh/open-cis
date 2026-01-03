from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class EncounterType(str, Enum):
    """Types of encounters based on FHIR/openEHR standards."""

    AMBULATORY = "ambulatory"
    EMERGENCY = "emergency"
    INPATIENT = "inpatient"
    VIRTUAL = "virtual"
    HOME = "home"
    FIELD = "field"


class EncounterStatus(str, Enum):
    """Status of the encounter."""

    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class EncounterCreate(BaseModel):
    """Schema for creating a new encounter."""

    patient_id: str
    type: EncounterType
    status: EncounterStatus
    start_time: datetime
    end_time: datetime | None = None
    reason: str | None = Field(None, max_length=500)
    provider_name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)

    @field_validator("end_time")
    @classmethod
    def end_time_after_start_time(cls, v: datetime | None, info: ValidationInfo) -> datetime | None:
        """Validate that end_time is after start_time."""
        if v is not None and "start_time" in info.data:
            if v < info.data["start_time"]:
                raise ValueError("end_time must be after start_time")
        return v


class EncounterUpdate(BaseModel):
    """Schema for updating an encounter."""

    type: EncounterType | None = None
    status: EncounterStatus | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    reason: str | None = Field(None, max_length=500)
    provider_name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)


class EncounterResponse(BaseModel):
    """Schema for encounter response."""

    id: str
    patient_id: str
    type: EncounterType
    status: EncounterStatus
    start_time: datetime
    end_time: datetime | None
    reason: str | None
    provider_name: str | None
    location: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
