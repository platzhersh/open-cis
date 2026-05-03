from typing import Any

from pydantic import BaseModel, Field


class SectionError(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class Section(BaseModel):
    """Envelope for a response section: {status, data, error}."""
    status: str = Field(..., description="ok | partial | error")
    data: Any = Field(None, description="Section payload (null when status is error)")
    error: SectionError | None = Field(
        None, description="Error details (null when status is ok)"
    )


class HealthCheckItem(BaseModel):
    status: str = Field(..., description="ok | error")
    data: dict[str, str] | None = Field(None, description="Health data")
    error: SectionError | None = None


class HealthChecksData(BaseModel):
    api: HealthCheckItem
    database: HealthCheckItem
    ehrbase: HealthCheckItem
    terminology: HealthCheckItem
    oidc: HealthCheckItem


class TemplateInfo(BaseModel):
    template_id: str = Field(..., description="openEHR template identifier")
    concept: str = Field(..., description="Template concept name")
    archetype_id: str = Field(..., description="Root archetype identifier")
    web_template_cached: bool = Field(
        False, description="Whether the Web Template is cached for FLAT path resolution"
    )


class VersionData(BaseModel):
    api: str = Field(..., description="Open CIS API version")
    ehrbase: str | None = Field(None, description="EHRBase version (null if unavailable)")
    oehrpy: str | None = Field(None, description="oehrpy SDK version (null if unavailable)")


class DbCountsData(BaseModel):
    patients: int = Field(..., description="Total registered patients")
    encounters: int = Field(..., description="Total encounters")
    audit_logs: int = Field(..., description="Total audit log entries")


class HealthChecksSection(BaseModel):
    status: str
    data: HealthChecksData
    error: SectionError | None = None


class VersionSection(BaseModel):
    status: str
    data: VersionData | None = None
    error: SectionError | None = None


class TemplatesSection(BaseModel):
    status: str
    data: list[TemplateInfo] | None = None
    error: SectionError | None = None


class DbCountsSection(BaseModel):
    status: str
    data: DbCountsData | None = None
    error: SectionError | None = None


class TerminologyData(BaseModel):
    url: str = Field(..., description="Configured terminology server URL")
    response_ms: int | None = Field(None, description="Response time in milliseconds")


class TerminologySection(BaseModel):
    status: str
    data: TerminologyData | None = None
    error: SectionError | None = None


class OidcData(BaseModel):
    issuer: str = Field(..., description="Configured OIDC issuer URL")
    client_id: str = Field(..., description="Configured OIDC client ID")
    discovery_url: str = Field(..., description="OIDC discovery document URL")
    jwks_uri: str | None = Field(None, description="JWKS endpoint URL")
    jwks_cached: bool = Field(False, description="Whether JWKS has been fetched and cached")
    response_ms: int | None = Field(
        None, description="Discovery endpoint response time in milliseconds"
    )


class OidcSection(BaseModel):
    status: str
    data: OidcData | None = None
    error: SectionError | None = None


class SystemInfoResponse(BaseModel):
    healthChecks: HealthChecksSection
    version: VersionSection
    templates: TemplatesSection
    dbCounts: DbCountsSection
    terminology: TerminologySection
    oidc: OidcSection
