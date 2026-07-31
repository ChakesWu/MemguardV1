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
