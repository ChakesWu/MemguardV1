import { createElement, type MouseEvent } from 'react'

import { OutputEvidenceLink } from '../../lib/agent-ui'

type EvidenceDetailPanelProps = {
  link: OutputEvidenceLink
  onClose: () => void
}

function row(label: string, value: string) {
  return createElement('div', { className: 'mg-evidence-panel__row', key: label }, [
    createElement('dt', { key: 'label' }, label),
    createElement('dd', { key: 'value' }, value),
  ])
}

export default function EvidenceDetailPanel({ link, onClose }: EvidenceDetailPanelProps) {
  const source = link.sourceType ? link.sourceType.replaceAll('_', ' ') : 'memory record'
  return createElement('div', { className: 'mg-evidence-panel-backdrop', onClick: onClose }, [
    createElement('aside', {
      className: 'mg-evidence-panel',
      role: 'dialog',
      'aria-modal': true,
      'aria-label': 'Full memory evidence',
      onClick: (event: MouseEvent<HTMLElement>) => event.stopPropagation(),
      key: 'panel',
    }, [
      createElement('header', { key: 'header' }, [
        createElement('div', { key: 'title' }, [
          createElement('p', { className: 'mg-eyebrow', key: 'eyebrow' }, 'Governed memory link'),
          createElement('h2', { key: 'heading' }, 'Full memory evidence'),
        ]),
        createElement('button', { type: 'button', className: 'mg-icon-button', 'aria-label': 'Close evidence panel', onClick: onClose, key: 'close' }, '×'),
      ]),
      createElement('p', { className: 'mg-evidence-panel__segment', key: 'segment' }, link.segment),
      createElement('dl', { key: 'details' }, [
        row('Memory ID', link.memoryId),
        row('Role in output', link.role.replaceAll('_', ' ')),
        row('Trust', `${link.trustScore ?? '—'} · ${link.trustLevel}`),
        row('Policy', link.policyAction.replaceAll('_', ' ')),
        row('Source', link.sourceId || source),
        row('Included in prompt', 'Yes'),
        row('Validated evidence', link.evidenceQuote),
      ]),
      createElement('button', { type: 'button', className: 'mg-button', onClick: onClose, key: 'dismiss' }, 'Close'),
    ]),
  ])
}
