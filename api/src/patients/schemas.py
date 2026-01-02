from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class PatientCreate(BaseModel):
    mrn: str = Field(
        ...,
        description=(
            "Medical Record Number (MRN) - Institution-specific patient identifier. "
            "See HL7 FHIR Patient.identifier "
            "(http://hl7.org/fhir/patient-definitions.html#Patient.identifier) "
            "and USCDI Medical Record Number data element."
        ),
    )
    given_name: str = Field(..., description="Patient's first/given name")
    family_name: str = Field(..., description="Patient's last/family name")
    birth_date: str | None = Field(
        None, description="Patient's date of birth (ISO 8601 format: YYYY-MM-DD)"
    )

    @field_validator("birth_date", mode="before")
    @classmethod
    def validate_birth_date(cls, v: str | None) -> str | None:
        """Validate and parse ISO date string to ensure correct format."""
        if v is None or v == "":
            return None
        try:
            # Validate it's a valid date by parsing it
            date.fromisoformat(v)
            return v
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid date format. Expected ISO 8601 (YYYY-MM-DD), got: {v}"
            ) from e


class PatientUpdate(BaseModel):
    given_name: str | None = Field(None, description="Patient's first/given name")
    family_name: str | None = Field(None, description="Patient's last/family name")
    birth_date: str | None = Field(
        None, description="Patient's date of birth (ISO 8601 format: YYYY-MM-DD)"
    )

    @field_validator("birth_date", mode="before")
    @classmethod
    def validate_birth_date(cls, v: str | None) -> str | None:
        """Validate and parse ISO date string to ensure correct format."""
        if v is None or v == "":
            return None
        try:
            # Validate it's a valid date by parsing it
            date.fromisoformat(v)
            return v
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid date format. Expected ISO 8601 (YYYY-MM-DD), got: {v}"
            ) from e


class PatientResponse(BaseModel):
    id: str = Field(..., description="Internal patient ID")
    mrn: str = Field(
        ...,
        description=(
            "Medical Record Number (MRN) - Institution-specific patient identifier. "
            "See HL7 FHIR Patient.identifier "
            "(http://hl7.org/fhir/patient-definitions.html#Patient.identifier) "
            "and USCDI Medical Record Number data element."
        ),
    )
    ehr_id: str = Field(..., description="EHRBase electronic health record ID")
    given_name: str = Field(..., description="Patient's first/given name")
    family_name: str = Field(..., description="Patient's last/family name")
    birth_date: str | None = Field(
        None, description="Patient's date of birth (ISO 8601 format: YYYY-MM-DD)"
    )
    created_at: datetime = Field(..., description="Timestamp when patient was created")
    updated_at: datetime = Field(..., description="Timestamp when patient was last updated")

    class Config:
        from_attributes = True
