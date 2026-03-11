export type CaveCategory = 'medication' | 'food' | 'environment' | 'other'
export type CaveReactionType = 'allergy' | 'intolerance' | 'unknown'
export type CaveCriticality = 'low' | 'high' | 'indeterminate'
export type CaveStatus = 'active' | 'inactive' | 'resolved' | 'refuted'
export type ReactionSeverity = 'mild' | 'moderate' | 'severe'
export type ReactionCertainty = 'suspected' | 'likely' | 'confirmed'

export interface ReactionEvent {
  manifestation: string
  severity: ReactionSeverity
  certainty: ReactionCertainty
  onset_date: string | null
  description: string | null
}

export interface CaveEntry {
  id: string
  ehr_id: string
  patient_id: string
  substance: string
  category: CaveCategory
  reaction_type: CaveReactionType
  criticality: CaveCriticality
  status: CaveStatus
  onset_date: string | null
  recorded_date: string
  last_updated: string
  comment: string | null
  reactions: ReactionEvent[]
  composition_uid: string
  template_id: string
  archetype_ids: string[]
}

export interface CaveEntryCreate {
  patient_id: string
  substance: string
  category: CaveCategory
  reaction_type: CaveReactionType
  criticality: CaveCriticality
  status?: CaveStatus
  onset_date?: string | null
  comment?: string | null
  reactions?: ReactionEvent[]
}

export interface CaveEntryUpdate {
  criticality?: CaveCriticality
  status?: CaveStatus
  comment?: string | null
  reactions?: ReactionEvent[]
}

export interface CaveListResponse {
  items: CaveEntry[]
  total: number
}

export interface CaveSummary {
  patient_id: string
  total_active: number
  has_high_criticality: boolean
  has_nka_declaration: boolean
  entries: CaveEntry[]
}

export const CAVE_CATEGORY_LABELS: Record<CaveCategory, string> = {
  medication: 'Medication',
  food: 'Food',
  environment: 'Environment',
  other: 'Other',
}

export const CAVE_CRITICALITY_LABELS: Record<CaveCriticality, string> = {
  low: 'Low',
  high: 'High',
  indeterminate: 'Indeterminate',
}

export const CAVE_STATUS_LABELS: Record<CaveStatus, string> = {
  active: 'Active',
  inactive: 'Inactive',
  resolved: 'Resolved',
  refuted: 'Refuted',
}

export const REACTION_TYPE_LABELS: Record<CaveReactionType, string> = {
  allergy: 'Allergy',
  intolerance: 'Intolerance',
  unknown: 'Unknown',
}

export const SEVERITY_LABELS: Record<ReactionSeverity, string> = {
  mild: 'Mild',
  moderate: 'Moderate',
  severe: 'Severe',
}

export const CERTAINTY_LABELS: Record<ReactionCertainty, string> = {
  suspected: 'Suspected',
  likely: 'Likely',
  confirmed: 'Confirmed',
}
