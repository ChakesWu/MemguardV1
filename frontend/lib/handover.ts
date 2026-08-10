export type HandoverOutcome = 'retained_at_source' | 'transferred' | 'protected' | 'redacted_for_review' | 'archived'

export interface HandoverItem {
  memory_id: string
  content: string
  redacted_content?: string | null
  owner: string
  transfer_policy: string
  business_owner: string
  source_label: string
  source_id?: string | null
  classification: string
  outcome: HandoverOutcome
  reason: string
  trust: { score: number | null; level: string; reason_codes: string[] }
  policy: { action: string; reason_codes: string[]; explanation: string }
  eligible_for_successor: boolean
}

export interface EnterpriseHandoverReport {
  tenant_id: string
  generated_at: string
  policy_id: string
  summary: Record<string, number>
  source_of_truth_ids: string[]
  successor_memory_ids: string[]
  successor_prompt: string
  items: HandoverItem[]
}

export function outcomeLabel(outcome: HandoverOutcome): string {
  return {
    retained_at_source: 'Stays at source',
    transferred: 'Transferred',
    protected: 'Protected',
    redacted_for_review: 'Review required',
    archived: 'Archived',
  }[outcome]
}
