from datetime import date, datetime

from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    mrn: str = Field(
        ...,
        description="Medical Record Number (MRN) - Institution-specific patient identifier. "
        "See HL7 FHIR Patient.identifier (http://hl7.org/fhir/patient-definitions.html#Patient.identifier) "
        "and USCDI Medical Record Number data element.",
    )
    given_name: str = Field(..., description="Patient's first/given name")
    family_name: str = Field(..., description="Patient's last/family name")
    birth_date: date | None = Field(None, description="Patient's date of birth")


class PatientUpdate(BaseModel):
    given_name: str | None = Field(None, description="Patient's first/given name")
    family_name: str | None = Field(None, description="Patient's last/family name")
    birth_date: date | None = Field(None, description="Patient's date of birth")


class PatientResponse(BaseModel):
    id: str = Field(..., description="Internal patient ID")
    mrn: str = Field(
        ...,
        description="Medical Record Number (MRN) - Institution-specific patient identifier. "
        "See HL7 FHIR Patient.identifier (http://hl7.org/fhir/patient-definitions.html#Patient.identifier) "
        "and USCDI Medical Record Number data element.",
    )
    ehr_id: str = Field(..., description="EHRBase electronic health record ID")
    given_name: str = Field(..., description="Patient's first/given name")
    family_name: str = Field(..., description="Patient's last/family name")
    birth_date: date | None = Field(None, description="Patient's date of birth")
    created_at: datetime = Field(..., description="Timestamp when patient was created")
    updated_at: datetime = Field(..., description="Timestamp when patient was last updated")

    class Config:
        from_attributes = True
