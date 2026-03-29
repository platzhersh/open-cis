from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    api: str = Field(..., description="Open CIS API version")
    ehrbase: str | None = Field(None, description="EHRBase version (null if unavailable)")


class HealthInfo(BaseModel):
    api: str = Field(..., description="API status: healthy or degraded")
    database: str = Field(..., description="Database status: connected or disconnected")
    ehrbase: str = Field(..., description="EHRBase status: available or unavailable")


class TemplateInfo(BaseModel):
    template_id: str = Field(..., description="openEHR template identifier")
    concept: str = Field(..., description="Template concept name")
    archetype_id: str = Field(..., description="Root archetype identifier")


class DataStats(BaseModel):
    patients: int = Field(..., description="Total registered patients")
    encounters: int = Field(..., description="Total encounters")
    audit_logs: int = Field(..., description="Total audit log entries")


class SystemInfoResponse(BaseModel):
    versions: VersionInfo
    health: HealthInfo
    templates: list[TemplateInfo] | None = Field(
        None, description="Registered templates (null if EHRBase unavailable)"
    )
    stats: DataStats | None = Field(
        None, description="Data statistics (null if database unavailable)"
    )
