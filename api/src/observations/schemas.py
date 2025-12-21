from datetime import datetime
from pydantic import BaseModel


class VitalSignsCreate(BaseModel):
    patient_id: str
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    respiratory_rate: float | None = None
    oxygen_saturation: float | None = None
    recorded_at: datetime | None = None


class VitalSignsResponse(BaseModel):
    composition_uid: str | None
    patient_id: str
    systolic_bp: float | None
    diastolic_bp: float | None
    heart_rate: float | None
    temperature: float | None
    respiratory_rate: float | None
    oxygen_saturation: float | None
    recorded_at: datetime


class ObservationResponse(BaseModel):
    id: str
    type: str
    value: float
    unit: str
    recorded_at: datetime
