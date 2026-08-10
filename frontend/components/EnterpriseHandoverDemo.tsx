'use client'

import { useMemo, useState } from 'react'

import { EnterpriseHandoverReport, HandoverItem, outcomeLabel } from '../lib/handover'

type EnterpriseHandoverDemoProps = {
  report: EnterpriseHandoverReport
}

function MemoryCard({ item, selected, onSelect }: { item: HandoverItem; selected: boolean; onSelect: () => void }) {
  return (
    <button type="button" className={`mg-handover-card ${selected ? 'is-selected' : ''}`} onClick={onSelect}>
      <span className={`mg-handover-outcome mg-handover-outcome--${item.outcome}`}>{outcomeLabel(item.outcome)}</span>
      <strong>{item.content}</strong>
      <span className="mg-handover-card__meta">{item.source_label} · {item.business_owner}</span>
    </button>
  )
}

export default function EnterpriseHandoverDemo({ report }: EnterpriseHandoverDemoProps) {
  const [selectedId, setSelectedId] = useState<string | null>(report.items[0]?.memory_id || null)
  const selected = useMemo(() => report.items.find(item => item.memory_id === selectedId) || null, [report.items, selectedId])
  const sourceItems = report.items.filter(item => item.outcome === 'retained_at_source')
  const employeeItems = report.items.filter(item => item.outcome !== 'retained_at_source')
  const successorItems = report.items.filter(item => item.eligible_for_successor)

  return (
    <main className="mg-handover-page">
      <header className="mg-handover-hero">
        <p className="mg-eyebrow">MemGuard / Enterprise memory handover</p>
        <h1>Keep company knowledge.<br />Protect the person behind it.</h1>
        <p>When Alex leaves, MemGuard decides what the next agent can safely inherit — and records why.</p>
      </header>

      <section className="mg-handover-metrics" aria-label="Handover results">
        <div><strong>{report.summary.transferred || 0}</strong><span>company memories transferred</span></div>
        <div><strong>{report.summary.protected || 0}</strong><span>personal memories protected</span></div>
        <div><strong>{report.summary.redacted_for_review || 0}</strong><span>records redacted for review</span></div>
        <div><strong>{report.summary.archived || 0}</strong><span>stale records archived</span></div>
      </section>

      <p className="mg-handover-instruction">Select any record to inspect its source, owner, policy decision, and what reaches the successor agent.</p>

      <section className="mg-handover-flow" aria-label="Enterprise memory boundary">
        <article className="mg-handover-lane mg-handover-lane--source">
          <header>
            <p className="mg-eyebrow">Read-only</p>
            <h2>Company source of truth</h2>
            <p>CRM and approved policy stay in the company system. Employee agents can read them; they cannot overwrite them.</p>
          </header>
          <div className="mg-handover-cards">
            {sourceItems.map(item => <MemoryCard key={item.memory_id} item={item} selected={selectedId === item.memory_id} onSelect={() => setSelectedId(item.memory_id)} />)}
          </div>
        </article>

        <div className="mg-handover-arrow" aria-hidden="true"><span>linked</span>→</div>

        <article className="mg-handover-lane">
          <header>
            <p className="mg-eyebrow">Leaving employee</p>
            <h2>Departing employee agent</h2>
            <p>Alex&apos;s agent has a private working memory as well as company knowledge. Ownership rules travel with every memory.</p>
          </header>
          <div className="mg-handover-cards">
            {employeeItems.map(item => <MemoryCard key={item.memory_id} item={item} selected={selectedId === item.memory_id} onSelect={() => setSelectedId(item.memory_id)} />)}
          </div>
        </article>

        <div className="mg-handover-arrow" aria-hidden="true"><span>MemGuard gate</span>→</div>

        <article className="mg-handover-lane mg-handover-lane--successor">
          <header>
            <p className="mg-eyebrow">Safe successor context</p>
            <h2>Successor team agent</h2>
            <p>Only approved company knowledge is added to the new team agent. Personal and sensitive memory never crosses this boundary.</p>
          </header>
          <div className="mg-handover-cards">
            {successorItems.map(item => <MemoryCard key={item.memory_id} item={item} selected={selectedId === item.memory_id} onSelect={() => setSelectedId(item.memory_id)} />)}
            {successorItems.length === 0 && <p className="mg-stage-empty">No memory was approved for transfer.</p>}
          </div>
          <p className="mg-handover-safe-note">0 protected or redacted records entered the successor agent.</p>
        </article>
      </section>

      {selected && (
        <aside className="mg-handover-panel" aria-label="Memory lineage">
          <header>
            <div>
              <p className="mg-eyebrow">Memory lineage</p>
              <h2>{selected.memory_id.replaceAll('-', ' ')}</h2>
            </div>
            <button type="button" className="mg-icon-button" aria-label="Close memory lineage" onClick={() => setSelectedId(null)}>×</button>
          </header>
          <p className="mg-handover-panel__content">{selected.content}</p>
          <dl className="mg-handover-details">
            <div><dt>Original source</dt><dd>{selected.source_label}{selected.source_id ? ` · ${selected.source_id}` : ''}</dd></div>
            <div><dt>Business owner</dt><dd>{selected.business_owner}</dd></div>
            <div><dt>Memory owner</dt><dd>{selected.owner.replaceAll('_', ' ')}</dd></div>
            <div><dt>Transfer policy</dt><dd>{selected.transfer_policy.replaceAll('_', ' ')}</dd></div>
            <div><dt>Trust evidence</dt><dd>{selected.trust.score === null ? 'Metadata incomplete' : `${selected.trust.score.toFixed(1)} · ${selected.trust.level}`}</dd></div>
            <div><dt>Policy decision</dt><dd>{selected.policy.action.replaceAll('_', ' ')}</dd></div>
            <div><dt>Successor access</dt><dd>{selected.eligible_for_successor ? 'Yes — approved company memory' : 'No — boundary enforced'}</dd></div>
          </dl>
          <section className="mg-handover-why">
            <p className="mg-eyebrow">Why this outcome</p>
            <p>{selected.reason}</p>
            <code>{selected.policy.reason_codes.join(' · ')}</code>
          </section>
        </aside>
      )}
    </main>
  )
}
