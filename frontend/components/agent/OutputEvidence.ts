import { createElement } from 'react'

import { OutputEvidenceLink, outputEvidenceParts } from '../../lib/agent-ui'

type OutputEvidenceProps = {
  answer: string
  links: OutputEvidenceLink[]
  onOpenEvidence?: (link: OutputEvidenceLink) => void
}

function sourceLabel(link: OutputEvidenceLink): string {
  return link.sourceType ? link.sourceType.replaceAll('_', ' ') : 'memory record'
}

function cardRow(label: string, value: string) {
  return createElement('span', { className: 'mg-evidence-card__row', key: label }, [
    createElement('b', { key: 'label' }, label),
    createElement('em', { key: 'value' }, value),
  ])
}

export default function OutputEvidence({ answer, links, onOpenEvidence }: OutputEvidenceProps) {
  const parts = outputEvidenceParts(answer, links)
  return createElement('p', { className: 'mg-agent-answer' }, parts.map((part, index) => {
    if (part.kind === 'text') return createElement('span', { key: `text-${index}` }, part.text)
    const primary = part.links[0]
    if (!primary) return createElement('span', { key: `empty-${index}` }, part.text)
    const source = sourceLabel(primary)
    return createElement('span', {
      className: 'mg-evidence-anchor',
      key: `evidence-${primary.startOffset}-${primary.endOffset}`,
    }, [
      createElement('span', { key: 'segment' }, part.text),
      createElement('span', { className: 'mg-evidence-chip', key: 'chip' }, [
        createElement('span', { className: 'mg-evidence-chip__icon', 'aria-hidden': true, key: 'icon' }, '▤'),
        createElement('span', { key: 'source' }, source),
        part.links.length > 1 ? createElement('strong', { key: 'count' }, `+${part.links.length - 1}`) : null,
      ]),
      createElement('span', { className: 'mg-evidence-card', role: 'group', 'aria-label': 'Memory evidence', key: 'card' }, [
        createElement('span', { className: 'mg-evidence-card__title', key: 'title' }, 'Memory evidence'),
        cardRow('Role in output', primary.role.replaceAll('_', ' ')),
        cardRow('Trust', `${primary.trustScore ?? '—'} · ${primary.trustLevel}`),
        cardRow('Policy', primary.policyAction.replaceAll('_', ' ')),
        cardRow('Source', primary.sourceId || source),
        cardRow('Included in prompt', 'Yes'),
        createElement('button', {
          type: 'button',
          className: 'mg-evidence-card__link',
          'aria-haspopup': 'dialog',
          onClick: () => onOpenEvidence?.(primary),
          key: 'link',
        }, 'Open full evidence ↗'),
      ]),
    ])
  }))
}
