import {
  DecisionTrace,
  ExplanationFinding,
  ExplanationStatus,
  traceOutput,
} from '../lib/dashboard'

interface WhyThisOutputProps {
  trace: DecisionTrace
}

const statusLabels: Record<ExplanationStatus, string> = {
  observed: 'OBSERVED · Recorded evidence',
  stale: 'INFERRED · Freshness limit exceeded',
  conflict: 'INFERRED · Conflicts with current input',
  stale_conflict: 'INFERRED · Stale and conflicting',
  evidence_gap: 'LIMIT · Evidence gap',
}

function displayValue(value: unknown): string {
  if (typeof value === 'string') return value
  if (value === undefined) return 'Unavailable'
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

function formatTimestamp(value?: string): string {
  if (!value) return 'Not recorded'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString()
}

function formatAge(seconds?: number): string | null {
  if (seconds === undefined) return null
  if (seconds < 60) return `${seconds} seconds`
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours`
  return `${Math.floor(seconds / 86400)} days`
}

function findingLabel(finding: ExplanationFinding): string {
  if (finding.included_in_prompt === false) {
    return 'OBSERVED · Retrieved but not included in context'
  }
  if (finding.kind === 'observed') {
    return 'OBSERVED · Retrieved and included in context'
  }
  return statusLabels[finding.kind]
}

function FindingCard({ finding, trace }: { finding: ExplanationFinding; trace: DecisionTrace }) {
  const evidence = trace.evidence_items?.find(item => item.event_id === finding.event_id)
  const hasComparison = finding.remembered_value !== undefined || finding.current_value !== undefined
  const age = formatAge(finding.age_seconds)

  return (
    <li className="mg-why-finding">
      <div className="mg-why-finding__header">
        <span className={`mg-explanation-status mg-explanation-status--${finding.kind}`}>
          {findingLabel(finding)}
        </span>
        <code>{finding.memory_key}</code>
      </div>

      {hasComparison ? (
        <div className="mg-value-comparison" aria-label="Remembered and current value comparison">
          <div>
            <span>Remembered value</span>
            <strong>{displayValue(finding.remembered_value)}</strong>
          </div>
          <div>
            <span>Current value</span>
            <strong>{displayValue(finding.current_value)}</strong>
          </div>
        </div>
      ) : evidence?.content_hash ? (
        <p className="mg-privacy-hidden">Content hidden by privacy mode · Hash {evidence.content_hash.slice(0, 12)}…</p>
      ) : null}

      <dl className="mg-provenance-grid">
        {finding.source_type && <div><dt>Source</dt><dd>{finding.source_type}</dd></div>}
        {finding.source_id && <div><dt>Record ID</dt><dd>{finding.source_id}</dd></div>}
        {finding.retrieval_rank !== undefined && <div><dt>Retrieval rank</dt><dd>#{finding.retrieval_rank}</dd></div>}
        {finding.retrieval_score !== undefined && <div><dt>Retrieval score</dt><dd>{finding.retrieval_score.toFixed(2)}</dd></div>}
        <div><dt>Prompt inclusion</dt><dd>{finding.included_in_prompt === false ? 'Excluded' : 'Included'}</dd></div>
        {finding.memory_created_at && (
          <div><dt>Created</dt><dd title={finding.memory_created_at}>{formatTimestamp(finding.memory_created_at)}</dd></div>
        )}
        {finding.memory_last_verified_at && (
          <div><dt>Last verified</dt><dd title={finding.memory_last_verified_at}>{formatTimestamp(finding.memory_last_verified_at)}</dd></div>
        )}
        {age && (
          <div><dt>Age at output</dt><dd title={`${finding.age_seconds} seconds`}>{age}</dd></div>
        )}
      </dl>
    </li>
  )
}

export default function WhyThisOutput({ trace }: WhyThisOutputProps) {
  const explanation = trace.explanation || {
    basis: 'recorded_evidence' as const,
    causality_claim: 'not_proven' as const,
    status: 'observed' as const,
    summary: 'Recorded evidence is available. A deterministic explanation was not stored for this older trace.',
    findings: [],
  }
  const missingEvidence = explanation.missing_evidence_event_ids || trace.missing_evidence_event_ids || []

  return (
    <section className="mg-why" aria-labelledby="mg-why-title">
      <header className="mg-why__header">
        <div>
          <p className="mg-eyebrow">Evidence-backed explanation</p>
          <h2 id="mg-why-title">Why this output?</h2>
        </div>
        <span className={`mg-explanation-status mg-explanation-status--${explanation.status}`}>
          {statusLabels[explanation.status]}
        </span>
      </header>

      <div className="mg-why__exchange">
        <article>
          <span>Current input</span>
          <p>{trace.user_input || 'No current input was recorded.'}</p>
        </article>
        <article>
          <span>Agent output</span>
          <p>{traceOutput(trace)}</p>
        </article>
      </div>

      <div className="mg-why__summary">
        <span>Deterministic finding</span>
        <p>{explanation.summary}</p>
      </div>

      {explanation.findings.length > 0 && (
        <ul className="mg-why__findings" aria-label="Memory explanation findings">
          {explanation.findings.map(finding => (
            <FindingCard key={finding.event_id} finding={finding} trace={trace} />
          ))}
        </ul>
      )}

      <div className="mg-why__limits">
        <p><strong>LIMIT</strong> · Recorded lineage is not proof of model causality.</p>
        {missingEvidence.length > 0 && (
          <div role="status">
            <strong>Missing linked evidence</strong>
            <code>{missingEvidence.join(', ')}</code>
          </div>
        )}
      </div>
    </section>
  )
}
