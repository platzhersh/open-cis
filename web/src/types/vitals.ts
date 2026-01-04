/**
 * Types for vital signs observations with openEHR transparency.
 */

export interface PathMapping {
  field: string
  archetype_id: string
  archetype_path: string
  flat_path: string
  value: number | string | null
  unit: string | null
}

export interface OpenEHRMetadata {
  composition_uid: string
  template_id: string
  archetype_ids: string[]
  ehr_id: string
  path_mappings: PathMapping[]
}

export interface VitalSignsReading {
  id: string // composition_uid
  patient_id: string
  encounter_id: string | null
  recorded_at: string // ISO 8601
  systolic: number | null
  diastolic: number | null
  pulse_rate: number | null
  created_at: string
  openehr_metadata: OpenEHRMetadata
}

export interface VitalSignsCreate {
  patient_id: string
  encounter_id?: string | null
  recorded_at: string // ISO 8601
  systolic?: number | null
  diastolic?: number | null
  pulse_rate?: number | null
}

export interface VitalSignsListResponse {
  items: VitalSignsReading[]
  total: number
}

export interface RawComposition {
  format: string
  template_id: string
  composition: Record<string, unknown>
}

export interface CompositionPath {
  path: string
  value: unknown
  type: string
}

export interface CompositionPathsResponse {
  composition_uid: string
  template_id: string
  paths: CompositionPath[]
}

export interface ArchetypeInfo {
  archetype_id: string
  concept: string
  description: string
  ckm_url: string | null
  reference_model: string
  type: string
}

export interface TemplateInfo {
  template_id: string
  concept: string | null
  archetype_id: string | null
}

export interface TemplateListResponse {
  templates: TemplateInfo[]
}

// Normal ranges for vital signs (WHO guidelines)
export const VITAL_SIGNS_NORMAL_RANGES = {
  systolic: { min: 90, max: 120, elevated: 139, high: 140 },
  diastolic: { min: 60, max: 80, elevated: 89, high: 90 },
  pulse_rate: { min: 60, max: 100 },
} as const

// Helper to determine if a value is in normal range
export function isInNormalRange(
  type: 'systolic' | 'diastolic' | 'pulse_rate',
  value: number
): boolean {
  const range = VITAL_SIGNS_NORMAL_RANGES[type]
  return value >= range.min && value <= range.max
}

// Helper to get status for BP values
export function getBPStatus(systolic: number, diastolic: number): 'normal' | 'elevated' | 'high' {
  const sysRange = VITAL_SIGNS_NORMAL_RANGES.systolic
  const diaRange = VITAL_SIGNS_NORMAL_RANGES.diastolic

  if (systolic >= sysRange.high || diastolic >= diaRange.high) {
    return 'high'
  }
  if (systolic > sysRange.max || diastolic > diaRange.max) {
    return 'elevated'
  }
  return 'normal'
}
