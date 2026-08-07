import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import EvidenceDetailPanel from '../components/agent/EvidenceDetailPanel'

describe('EvidenceDetailPanel', () => {
  it('renders the selected evidence in a persistent dialog', () => {
    const markup = renderToStaticMarkup(
      createElement(EvidenceDetailPanel, {
        link: {
          startOffset: 0,
          endOffset: 8,
          segment: 'ORD-4821',
          memoryId: 'order:ORD-4821',
          evidenceQuote: '[hash-only]',
          role: 'factual_support',
          trustScore: 100,
          trustLevel: 'high',
          policyAction: 'allow',
          sourceType: 'support_order',
          sourceId: 'ORD-4821',
        },
        onClose: () => undefined,
      }),
    )

    expect(markup).toContain('role="dialog"')
    expect(markup).toContain('Full memory evidence')
    expect(markup).toContain('ORD-4821')
    expect(markup).toContain('100 · high')
    expect(markup).toContain('Close')
  })
})
