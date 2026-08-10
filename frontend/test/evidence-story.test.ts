import { describe, expect, it } from 'vitest'

import { DecisionTrace, GovernedMemory, EvidenceItem, evidenceStory, memoryUsage } from '../lib/dashboard'

const trace: DecisionTrace = {
  trace_id: 'trace-1', agent_id: 'support', session_id: 'thread-1', timestamp: '2026-08-09T00:00:00Z',
  total_influence_score: 0.8, input_memory_ids: ['order:ORD-4821'], output_memory_ids: [],
  llm_output: 'Your order was delivered and paid.', user_input: 'Refund please',
}

const order: GovernedMemory = {
  memory_id: 'order:ORD-4821', kind: 'support_order', display_name: 'Noise-cancelling headphones order',
  summary: 'Delivered July 5, 2026 · Payment paid', source_type: 'support_order_db', source_id: 'ORD-4821',
  writer_id: 'support-order-sync', conflict_status: 'none', trust_score: 94.67, trust_level: 'high',
  trust_factors: {}, policy_status: 'allow', policy_explanation: 'Verified company order record.', prompt_eligible: true,
}

it('explains a linked memory as a human-readable claim evidence story', () => {
  const event: EvidenceItem = {
    event_id: 'event-1', memory_key: order.memory_id, operation: 'read',
    metadata: {
      evidence_quote: 'delivered July 5, 2026; payment paid',
      output_segment: 'Your order was delivered and paid.',
      evidence_role: 'factual_support',
    },
  }

  expect(evidenceStory(event, order)).toMatchObject({
    memoryTitle: 'Noise-cancelling headphones order',
    supportsClaim: 'Your order was delivered and paid.',
    evidenceQuote: 'delivered July 5, 2026; payment paid',
    roleDescription: 'Establishes a fact stated in the answer.',
  })
})

it('distinguishes used, rejected, and merely available memory without guessing causality', () => {
  const expired = { ...order, memory_id: 'MEM-EXCEPTION-77', prompt_eligible: false, policy_status: 'block' }
  const available = { ...order, memory_id: 'policy:refund-policy:v2' }

  expect(memoryUsage(order, trace)).toBe('used')
  expect(memoryUsage(expired, trace)).toBe('rejected')
  expect(memoryUsage(available, trace)).toBe('available')
})
