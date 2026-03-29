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

export interface PatientUpdate {
  given_name?: string
  family_name?: string
  birth_date?: string | null
}

export interface MrnExistsResponse {
  exists: boolean
}

export interface Observation {
  id: string
  type: string
  value: number
  unit: string
  recorded_at: string
}

export type EncounterType =
  | 'ambulatory'
  | 'emergency'
  | 'inpatient'
  | 'virtual'
  | 'home'
  | 'field'

export type EncounterStatus = 'planned' | 'in-progress' | 'finished' | 'cancelled'

export interface Encounter {
  id: string
  patient_id: string
  type: EncounterType
  status: EncounterStatus
  start_time: string
  end_time: string | null
  reason: string | null
  provider_name: string | null
  location: string | null
  created_at: string
  updated_at: string
}

export interface EncounterCreate {
  patient_id: string
  type: EncounterType
  status: EncounterStatus
  start_time: string
  end_time?: string | null
  reason?: string | null
  provider_name?: string | null
  location?: string | null
}

export interface EncounterUpdate {
  type?: EncounterType
  status?: EncounterStatus
  start_time?: string
  end_time?: string | null
  reason?: string | null
  provider_name?: string | null
  location?: string | null
}

// System info types — partial-failure envelope {status, data, error}

export interface SectionError {
  code: string
  message: string
}

export interface HealthCheckItem {
  status: 'ok' | 'error'
  data: { status: string } | null
  error: SectionError | null
}

export interface HealthChecksData {
  api: HealthCheckItem
  database: HealthCheckItem
  ehrbase: HealthCheckItem
}

export interface HealthChecksSection {
  status: 'ok' | 'partial' | 'error'
  data: HealthChecksData
  error: SectionError | null
}

export interface VersionData {
  api: string
  ehrbase: string | null
}

export interface VersionSection {
  status: 'ok' | 'partial' | 'error'
  data: VersionData | null
  error: SectionError | null
}

export interface TemplateInfo {
  template_id: string
  concept: string
  archetype_id: string
}

export interface TemplatesSection {
  status: 'ok' | 'error'
  data: TemplateInfo[] | null
  error: SectionError | null
}

export interface DbCountsData {
  patients: number
  encounters: number
  audit_logs: number
}

export interface DbCountsSection {
  status: 'ok' | 'error'
  data: DbCountsData | null
  error: SectionError | null
}

export interface SystemInfo {
  healthChecks: HealthChecksSection
  version: VersionSection
  templates: TemplatesSection
  dbCounts: DbCountsSection
}

// Re-export vitals types
export * from './vitals'
