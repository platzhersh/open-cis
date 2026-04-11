"""Response schemas for terminology endpoints."""

from pydantic import BaseModel, Field


class TerminologyHealthResponse(BaseModel):
    status: str = Field(..., description="online | degraded | offline")
    url: str = Field(..., description="Configured terminology server URL")
    response_ms: int | None = Field(None, description="Response time in milliseconds")


class CodeLookupResponse(BaseModel):
    system: str
    code: str
    display: str | None = None
    found: bool
