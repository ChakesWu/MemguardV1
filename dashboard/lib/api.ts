import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface MemoryEvent {
  event_id: string
  agent_id: string
  session_id: string
  operation: string
  memory_key: string
  memory_type: string
  content_hash: string
  timestamp: string
  context?: Record<string, any>
}

export interface DecisionTrace {
  trace_id: string
  agent_id: string
  timestamp: string
  input_memory_influences: MemoryInfluence[]
  total_input_influence: number
  decision_type: string
  decision_confidence: number
  decision_reasoning: string
  key_factors: string[]
  output_memory_influences: MemoryOutput[]
}

export interface MemoryInfluence {
  memory_key: string
  memory_type: string
  operation: string
  influence_score: number
  content_preview?: string
  similarity_score?: number
}

export interface MemoryOutput {
  memory_key: string
  memory_type: string
  operation: string
  content_hash: string
}

export interface Stats {
  total_events: number
  total_decision_traces: number
}

export const api = {
  async getEvents(params?: { limit?: number; offset?: number }): Promise<{ events: MemoryEvent[]; total: number }> {
    const response = await axios.get(`${API_BASE_URL}/v1/events`, { params })
    return response.data
  },

  async getStats(): Promise<Stats> {
    const response = await axios.get(`${API_BASE_URL}/v1/db/stats`)
    return response.data
  },

  async getDecisionTrace(traceId: string): Promise<DecisionTrace> {
    const response = await axios.get(`${API_BASE_URL}/v1/decision-traces/${traceId}`)
    return response.data
  },

  async health(): Promise<{ status: string }> {
    const response = await axios.get(`${API_BASE_URL}/health`)
    return response.data
  },
}
