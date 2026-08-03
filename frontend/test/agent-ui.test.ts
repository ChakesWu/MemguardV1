import { describe, expect, it } from 'vitest'

import { parseApprovalInterrupt, messageText } from '../lib/agent-ui'

describe('agent UI helpers', () => {
  it('recognizes the approval interrupt emitted by the refund tool', () => {
    expect(parseApprovalInterrupt({
      kind: 'approval_required',
      action: 'request_refund',
      arguments: { order_id: 'ORD-4821' },
      policy_decision: 'manual_review',
      policy_version: 'v2',
      allowed_decisions: ['approve', 'edit', 'reject'],
    })).toMatchObject({ action: 'request_refund', policyDecision: 'manual_review' })
  })

  it('does not render unknown interrupt data as an approval card', () => {
    expect(parseApprovalInterrupt({ kind: 'other' })).toBeNull()
  })

  it('renders text from either string or structured LangChain message content', () => {
    expect(messageText('A refund needs review.')).toBe('A refund needs review.')
    expect(messageText([{ type: 'text', text: 'Current policy applies.' }])).toBe('Current policy applies.')
  })
})
