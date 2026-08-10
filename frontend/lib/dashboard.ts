export interface MemoryEvent {
  event_id: string
  agent_id: string
  session_id: string
  operation: string
  memory_key: string
  namespace: string
  memory_type: string
  content_hash: string
  timestamp: string
  context?: Record<string, any>
  before_value?: any
  after_value?: any
}

export interface Conflict {
  memory_key: string
  agent_a: string
  agent_b: string
  delta_seconds: number
  severity: 'critical' | 'high' | 'medium'
  same_content: boolean
  time_a: string
  time_b: string
  event_a: string
  event_b: string
}

export interface Stats {
  total_events: number
  total_decision_traces: number
  database_driver?: string
  db_path?: string
}

export interface GovernedMemory {
  memory_id: string
  kind: string
  display_name: string
  summary: string
  source_type: string
  source_id?: string
  writer_id?: string
  verified_at?: string
  updated_at?: string
  conflict_status: string
  trust_score: number | null
  trust_level: string
  trust_factors: Record<string, { score: number | null; reason: string }>
  policy_status: string
  policy_explanation: string
  policy_reason_codes?: string[]
  prompt_eligible: boolean
}

export interface EvidenceItem {
  event_id: string
  side?: 'input' | 'output'
  agent_id?: string
  memory_key: string
  operation: string
  memory_type?: string
  timestamp?: string
  content_hash?: string
  metadata?: Record<string, any>
}

export interface DecisionTrace {
  trace_id: string
  agent_id: string
  session_id: string
  timestamp: string
  total_influence_score: number
  input_memory_ids: string[]
  input_memory_events?: string[]
  output_memory_ids: string[]
  output_memory_events?: string[]
  input_memory_details?: EvidenceItem[]
  output_memory_details?: EvidenceItem[]
  evidence_items?: EvidenceItem[]
  missing_evidence_event_ids?: string[]
  llm_output: string
  user_input: string
  memory_influence_scores?: Record<string, number>
  metadata?: Record<string, any>
  output_summary?: string
}

export interface MemoryKeyPresentation {
  label: string
  category: string
}

export function inputEvidence(trace: DecisionTrace): EvidenceItem[] {
  if (trace.evidence_items) {
    return trace.evidence_items.filter(item => item.side === 'input')
  }
  return trace.input_memory_details || []
}

export function outputEvidence(trace: DecisionTrace): EvidenceItem[] {
  if (trace.evidence_items) {
    return trace.evidence_items.filter(item => item.side === 'output')
  }
  return trace.output_memory_details || []
}

export function evidenceContextLabel(detail: EvidenceItem): string {
  const metadata = detail.metadata || {}
  const parts: string[] = []

  if (metadata.source_type) parts.push(`source ${metadata.source_type}`)
  if (metadata.evidence_role) parts.push(`role ${metadata.evidence_role}`)
  if (metadata.relevance) parts.push(`relevance ${metadata.relevance}`)
  if (metadata.trust_score !== undefined) parts.push(`trust ${metadata.trust_score}`)
  if (metadata.policy_status) parts.push(`policy ${metadata.policy_status}`)

  return parts.join(' · ')
}

export function memoryKeyPresentation(key: string): MemoryKeyPresentation {
  const separator = key.indexOf(':')
  if (separator === -1) return { label: key, category: 'memory' }

  return {
    category: key.slice(0, separator),
    label: key.slice(separator + 1),
  }
}

export function traceOutput(trace: DecisionTrace): string {
  return trace.llm_output || trace.output_summary || trace.user_input || 'No output recorded'
}

export type MemoryUsage = 'used' | 'constrained' | 'rejected' | 'available'

export interface HumanEvidenceStory {
  memoryTitle: string
  memorySummary: string
  supportsClaim: string | null
  evidenceQuote: string | null
  roleDescription: string
  whyAllowed: string
}

export function memoryUsage(memory: GovernedMemory, trace: DecisionTrace | null): MemoryUsage {
  if (trace) {
    const considered = Array.isArray(trace.metadata?.considered_memories)
      ? trace.metadata?.considered_memories as Array<Record<string, unknown>>
      : []
    const recorded = considered.find(item => item.memory_id === memory.memory_id)
    if (recorded && ['used', 'constrained', 'rejected', 'available'].includes(String(recorded.usage))) {
      return recorded.usage as MemoryUsage
    }
    if ((trace.input_memory_ids || []).includes(memory.memory_id)) return 'used'
  }
  if (!memory.prompt_eligible || ['block', 'quarantine', 'review_required'].includes(memory.policy_status)) return 'rejected'
  return 'available'
}

export function evidenceStory(item: EvidenceItem, memory?: GovernedMemory): HumanEvidenceStory {
  const metadata = item.metadata || {}
  const role = String(metadata.evidence_role || '')
  const roleDescription = {
    factual_support: 'Establishes a fact stated in the answer.',
    constraint: 'Limits what the agent may say or do.',
    preference: 'Applies a recorded customer or business preference.',
    background_context: 'Provides relevant context without proving the claim by itself.',
  }[role] || 'Recorded as governed context for this answer.'
  const factors = memory?.trust_factors || metadata.trust_factors || {}
  const sourceReason = factors.source?.reason
  const writerReason = factors.writer?.reason
  const freshnessReason = factors.freshness?.reason
  const conflictReason = factors.conflict?.reason
  const reasons = [sourceReason, writerReason, freshnessReason, conflictReason].filter(Boolean)
  return {
    memoryTitle: memory?.display_name || memoryKeyPresentation(item.memory_key).label || item.memory_key,
    memorySummary: memory?.summary || String(item.metadata?.memory_summary || 'The raw memory summary was not captured for this older event.'),
    supportsClaim: typeof metadata.output_segment === 'string' ? metadata.output_segment : null,
    evidenceQuote: typeof metadata.evidence_quote === 'string' ? metadata.evidence_quote : null,
    roleDescription,
    whyAllowed: reasons.length
      ? reasons.join(' · ')
      : memory?.policy_explanation || String(metadata.policy_explanation || 'Governance explanation was not captured for this older event.'),
  }
}
