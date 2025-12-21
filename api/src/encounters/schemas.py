from datetime import datetime
from pydantic import BaseModel


class EncounterCreate(BaseModel):
    patient_id: str
    encounter_type: str
    start_time: datetime | None = None
    notes: str | None = None


class EncounterUpdate(BaseModel):
    encounter_type: str | None = None
    end_time: datetime | None = None
    notes: str | None = None


class EncounterResponse(BaseModel):
    id: str
    patient_id: str
    ehr_id: str
    composition_uid: str | None
    encounter_type: str
    start_time: datetime
    end_time: datetime | None
    notes: str | None

    class Config:
        from_attributes = True
