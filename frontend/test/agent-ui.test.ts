import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { outputEvidenceParts, parseApprovalInterrupt, parseMessageOutputEvidence, parseOutputEvidence, messageText, shouldRenderChatMessage } from '../lib/agent-ui'

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

  it('accepts only explicit, prompt-included evidence whose offsets match the output', () => {
    const answer = 'ORD-4821 is eligible for manual review.'

    expect(parseOutputEvidence(answer, {
      items: [{
        memory_id: 'MEM-ORDER-4821-v1',
        source: { type: 'support_order', id: 'ORD-4821' },
      }],
      output_evidence: { valid_links: [{
        start_offset: 0,
        end_offset: 8,
        segment: 'ORD-4821',
        memory_id: 'MEM-ORDER-4821-v1',
        evidence_quote: 'Order ORD-4821 is delivered.',
        role: 'factual_support',
        prompt_included: true,
        validation_status: 'valid',
        trust: { score: 88, level: 'high' },
        policy: { action: 'allow' },
      }], },
    })).toEqual([expect.objectContaining({
      memoryId: 'MEM-ORDER-4821-v1',
      segment: 'ORD-4821',
      trustScore: 88,
      policyAction: 'allow',
    })])
  })

  it('rejects a citation when its text does not match the visible output', () => {
    expect(parseOutputEvidence('The order is eligible.', {
      items: [],
      output_evidence: { valid_links: [{
        start_offset: 0,
        end_offset: 9,
        segment: 'Wrong text',
        memory_id: 'MEM-ORDER-4821-v1',
        evidence_quote: 'Order is eligible.',
        role: 'factual_support',
        prompt_included: true,
        validation_status: 'valid',
        trust: { score: 88, level: 'high' },
        policy: { action: 'allow' },
      }], },
    })).toEqual([])
  })

  it('places an evidence chip immediately after the cited output segment', () => {
    const link = parseOutputEvidence('ORD-4821 is eligible.', {
      items: [],
      output_evidence: { valid_links: [{
        start_offset: 0,
        end_offset: 8,
        segment: 'ORD-4821',
        memory_id: 'MEM-ORDER-4821-v1',
        evidence_quote: '[hash-only]',
        role: 'factual_support',
        prompt_included: true,
        validation_status: 'valid',
        trust: { score: 88, level: 'high' },
        policy: { action: 'allow' },
      }] },
    })

    expect(outputEvidenceParts('ORD-4821 is eligible.', link)).toEqual([
      { kind: 'evidence', text: 'ORD-4821', links: link },
      { kind: 'text', text: ' is eligible.' },
    ])
  })

  it('reads the evidence report only from the agent message MemGuard metadata field', () => {
    const links = parseMessageOutputEvidence('Order details are verified.', {
      additional_kwargs: {
        memguard_output_evidence: {
          items: [],
          output_evidence: { valid_links: [{
            start_offset: 0,
            end_offset: 13,
            segment: 'Order details',
            memory_id: 'MEM-ORDER-v1',
            evidence_quote: '[hash-only]',
            role: 'factual_support',
            prompt_included: true,
            validation_status: 'valid',
            trust: { score: 92, level: 'high' },
            policy: { action: 'allow' },
          }] },
        },
      },
    })

    expect(links).toHaveLength(1)
    expect(links[0].memoryId).toBe('MEM-ORDER-v1')
  })

  it('does not subscribe to the unsupported legacy tools stream mode', () => {
    const chatSource = readFileSync(join(process.cwd(), 'components/agent/SupportAgentChat.tsx'), 'utf8')

    expect(chatSource).not.toContain('stream.toolProgress')
  })

  it('does not render tool result messages as support chat turns', () => {
    expect(shouldRenderChatMessage({
      type: 'tool',
      content: '{"status":"found","order_id":"ORD-4821"}',
    })).toBe(false)
    expect(shouldRenderChatMessage({ type: 'human', content: 'Refund ORD-4821' })).toBe(true)
    expect(shouldRenderChatMessage({ type: 'ai', content: 'I found ORD-4821.' })).toBe(true)
  })
})
