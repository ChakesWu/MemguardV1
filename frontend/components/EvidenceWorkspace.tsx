import {
  DecisionTrace,
  EvidenceItem,
  evidenceContextLabel,
  inputEvidence,
  memoryKeyPresentation,
  outputEvidence,
  traceOutput,
} from '../lib/dashboard'
import WhyThisOutput from './WhyThisOutput'

interface EvidenceWorkspaceProps {
  trace: DecisionTrace | null
}

function EvidenceRecord({ item, direction }: { item: EvidenceItem; direction: 'input' | 'output' }) {
  const key = memoryKeyPresentation(item.memory_key || '')
  const context = evidenceContextLabel(item)

  return (
    <li className="mg-evidence-record">
      <div className="mg-evidence-record__topline">
        <span className="mg-evidence-record__type">{item.memory_type || key.category}</span>
        <span className={`mg-status mg-status--${direction}`}>
          {direction === 'input' ? item.operation : item.operation || 'write'}
        </span>
      </div>
      <code className="mg-evidence-record__key">{key.label || item.memory_key}</code>
      <div className="mg-evidence-record__meta">
        <span>{item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Timestamp unavailable'}</span>
        <span>Event {item.event_id}</span>
        {item.content_hash && <span>Hash {item.content_hash.slice(0, 12)}…</span>}
      </div>
      {context && <p className="mg-evidence-record__context">{context}</p>}
    </li>
  )
}

export default function EvidenceWorkspace({ trace }: EvidenceWorkspaceProps) {
  if (!trace) {
    return (
      <main className="mg-workspace mg-workspace--empty">
        <div className="mg-empty-state">
          <p className="mg-eyebrow">No output selected</p>
          <h1>Record an agent output to inspect its evidence.</h1>
          <p>Run the deterministic memory demo with an authenticated MemGuard token, then refresh this workspace.</p>
          <code>
            memguard demo --api-url http://localhost:8000 --api-token &lt;token&gt; --tenant-id acme-dev
          </code>
        </div>
      </main>
    )
  }

  const persistedEvidence = trace.evidence_items
  const evidenceInputs = persistedEvidence
    ? persistedEvidence.filter(item => item.side === 'input')
    : inputEvidence(trace)
  const evidenceOutputs = persistedEvidence
    ? persistedEvidence.filter(item => item.side === 'output')
    : outputEvidence(trace)
  const missingEvidence = trace.missing_evidence_event_ids || []
  const ranking = trace.total_influence_score || 0

  return (
    <main className="mg-workspace">
      <header className="mg-workspace__header">
        <div>
          <p className="mg-eyebrow">Trace / {trace.trace_id}</p>
          <h1>Why did it output this?</h1>
        </div>
        <dl className="mg-trace-meta">
          <div><dt>Agent</dt><dd>{trace.agent_id}</dd></div>
          <div><dt>Session</dt><dd>{trace.session_id}</dd></div>
          <div><dt>Generated</dt><dd>{new Date(trace.timestamp).toLocaleString()}</dd></div>
        </dl>
      </header>

      <WhyThisOutput trace={trace} />

      <div className="mg-section-heading">
        <h2>Evidence lineage</h2>
        <p>Every displayed item is backed by the trace API.</p>
      </div>

      <section className="mg-lineage" aria-label="Evidence lineage">
        <article className="mg-lineage-stage">
          <header><h3>Available evidence</h3><span>{evidenceInputs.length} items</span></header>
          {evidenceInputs.length > 0 ? (
            <ul>{evidenceInputs.map(item => <EvidenceRecord key={item.event_id} item={item} direction="input" />)}</ul>
          ) : (
            <p className="mg-stage-empty">No persisted input evidence is linked to this output.</p>
          )}
        </article>

        <div className="mg-lineage-arrow" aria-hidden="true">→</div>

        <article className="mg-lineage-stage mg-lineage-stage--output">
          <header><h3>Agent output</h3><span>{ranking.toFixed(2)} rank</span></header>
          <div className="mg-lineage-output">
            <p>{traceOutput(trace)}</p>
            <dl>
              <div><dt>Evidence linked</dt><dd>{evidenceInputs.length}</dd></div>
              <div><dt>Missing records</dt><dd>{missingEvidence.length}</dd></div>
            </dl>
          </div>
        </article>

        <div className="mg-lineage-arrow" aria-hidden="true">→</div>

        <article className="mg-lineage-stage">
          <header><h3>Resulting memory writes</h3><span>{evidenceOutputs.length} items</span></header>
          {evidenceOutputs.length > 0 ? (
            <ul>{evidenceOutputs.map(item => <EvidenceRecord key={item.event_id} item={item} direction="output" />)}</ul>
          ) : (
            <p className="mg-stage-empty">No resulting memory writes were recorded.</p>
          )}
        </article>
      </section>

      {missingEvidence.length > 0 && (
        <section className="mg-evidence-gap" role="status">
          <strong>Evidence gap</strong>
          <p>{missingEvidence.length} linked event record{missingEvidence.length === 1 ? ' is' : 's are'} unavailable. MemGuard has not inferred or fabricated replacements.</p>
          <code>{missingEvidence.join(', ')}</code>
        </section>
      )}
    </main>
  )
}
