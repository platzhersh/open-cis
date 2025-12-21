export interface Patient {
  id: string
  mrn: string
  ehr_id: string
  given_name: string
  family_name: string
  birth_date: string | null
  created_at: string
  updated_at: string
}

export interface PatientCreate {
  mrn: string
  given_name: string
  family_name: string
  birth_date?: string
}

export interface Observation {
  id: string
  type: string
  value: number
  unit: string
  recorded_at: string
}

export interface Encounter {
  id: string
  type: string
  start_time: string
  end_time?: string
}
