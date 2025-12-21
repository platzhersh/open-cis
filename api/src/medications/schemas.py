from datetime import datetime
from pydantic import BaseModel


class MedicationOrderCreate(BaseModel):
    patient_id: str
    medication_name: str
    dose: str
    dose_unit: str
    frequency: str
    route: str | None = None
    instructions: str | None = None


class MedicationOrderResponse(BaseModel):
    composition_uid: str | None
    patient_id: str
    medication_name: str
    dose: str
    dose_unit: str
    frequency: str
    route: str | None
    instructions: str | None
    ordered_at: datetime
    status: str


class MedicationListItem(BaseModel):
    composition_id: str
    medication_name: str
    dose: str
