"""Schemas for vital signs observations with openEHR transparency."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class PathMappingResponse(BaseModel):
    """Maps a UI field to its openEHR path."""

    field: str
    archetype_id: str
    archetype_path: str
    flat_path: str
    value: float | int | str | None
    unit: str | None = None


class OpenEHRMetadataResponse(BaseModel):
    """openEHR metadata for transparency."""

    composition_uid: str
    template_id: str
    archetype_ids: list[str]
    ehr_id: str
    path_mappings: list[PathMappingResponse]


class VitalSignsCreate(BaseModel):
    """Request to record vital signs."""

    patient_id: str
    encounter_id: str | None = None  # Optional - vital signs can be recorded without encounter
    recorded_at: datetime

    # Blood pressure (optional - can record just pulse)
    systolic: int | None = Field(None, ge=50, le=300, description="Systolic BP in mmHg")
    diastolic: int | None = Field(None, ge=30, le=200, description="Diastolic BP in mmHg")

    # Pulse (optional - can record just BP)
    pulse_rate: int | None = Field(None, ge=20, le=300, description="Pulse rate in bpm")

    @field_validator("recorded_at")
    @classmethod
    def validate_not_future(cls, v: datetime) -> datetime:
        """Validate that recorded_at is not in the future."""
        now = datetime.now(UTC)
        # Make v timezone-aware if it's naive
        v_aware = v if v.tzinfo is not None else v.replace(tzinfo=UTC)
        if v_aware > now:
            raise ValueError("recorded_at cannot be in the future")
        return v

    @model_validator(mode="after")
    def validate_vitals(self) -> "VitalSignsCreate":
        """Validate that at least one vital is provided and BP is complete."""
        has_bp = self.systolic is not None or self.diastolic is not None
        has_pulse = self.pulse_rate is not None

        if not has_bp and not has_pulse:
            raise ValueError("At least one vital sign must be provided")

        if (self.systolic is None) != (self.diastolic is None):
            raise ValueError("Both systolic and diastolic must be provided together")

        return self


class VitalSignsResponse(BaseModel):
    """Response for a vital signs reading."""

    id: str  # composition_uid
    patient_id: str
    encounter_id: str | None
    recorded_at: datetime
    systolic: int | None
    diastolic: int | None
    pulse_rate: int | None
    created_at: datetime
    openehr_metadata: OpenEHRMetadataResponse


class VitalSignsListResponse(BaseModel):
    """Paginated list of vital signs readings."""

    items: list[VitalSignsResponse]
    total: int


class RawCompositionResponse(BaseModel):
    """Raw composition data for transparency."""

    format: str
    template_id: str
    composition: dict


class TemplateInfo(BaseModel):
    """Template information."""

    template_id: str
    concept: str | None = None
    archetype_id: str | None = None


class TemplateListResponse(BaseModel):
    """List of available templates."""

    templates: list[TemplateInfo]
