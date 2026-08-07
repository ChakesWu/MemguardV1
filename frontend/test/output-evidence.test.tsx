import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import OutputEvidence from '../components/agent/OutputEvidence'

describe('OutputEvidence', () => {
  it('renders an inline chip with an auditable memory card for validated evidence', () => {
    const markup = renderToStaticMarkup(
      createElement(OutputEvidence, {
        answer: 'ORD-4821 is eligible.',
        links: [{
          startOffset: 0,
          endOffset: 8,
          segment: 'ORD-4821',
          memoryId: 'MEM-ORDER-4821-v1',
          evidenceQuote: '[hash-only]',
          role: 'factual_support',
          trustScore: 88,
          trustLevel: 'high',
          policyAction: 'allow',
          sourceType: 'support_order',
          sourceId: 'ORD-4821',
        }],
      }),
    )

    expect(markup).toContain('ORD-4821')
    expect(markup).toContain('Memory evidence')
    expect(markup).toContain('Trust')
    expect(markup).toContain('88')
    expect(markup).toContain('Included in prompt')
    expect(markup).toContain('aria-haspopup="dialog"')
    expect(markup).toContain('Open full evidence')
  })
})
