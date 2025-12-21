from datetime import date, datetime
from pydantic import BaseModel, EmailStr


class PatientCreate(BaseModel):
    mrn: str
    given_name: str
    family_name: str
    birth_date: date | None = None


class PatientUpdate(BaseModel):
    given_name: str | None = None
    family_name: str | None = None
    birth_date: date | None = None


class PatientResponse(BaseModel):
    id: str
    mrn: str
    ehr_id: str
    given_name: str
    family_name: str
    birth_date: date | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
