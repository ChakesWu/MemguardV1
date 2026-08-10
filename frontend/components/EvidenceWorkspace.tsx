import {
  DecisionTrace,
  EvidenceItem,
  GovernedMemory,
  evidenceStory,
  inputEvidence,
  memoryUsage,
  traceOutput,
} from '../lib/dashboard'

interface EvidenceWorkspaceProps {
  trace: DecisionTrace | null
  inventory: GovernedMemory[]
}

function HighlightedAnswer({ answer, evidence }: { answer: string; evidence: EvidenceItem[] }) {
  const segments = evidence
    .map(item => item.metadata?.output_segment)
    .filter((segment): segment is string => typeof segment === 'string' && segment.length > 0)
  if (!segments.length) return <p>{answer}</p>

  const pattern = new RegExp(`(${segments.map(segment => segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'g')
  return <p>{answer.split(pattern).map((part, index) => segments.includes(part) ? <mark key={index}>{part}</mark> : part)}</p>
}

function EvidenceStoryCard({ item, memory }: { item: EvidenceItem; memory?: GovernedMemory }) {
  const story = evidenceStory(item, memory)
  return (
    <article className="mg-story-card">
      <div className="mg-story-card__step"><span>1</span><div><small>Agent said</small><strong>{story.supportsClaim || 'Claim-level segment was not captured for this older event.'}</strong></div></div>
      <div className="mg-story-card__connector" aria-hidden="true" />
      <div className="mg-story-card__step"><span>2</span><div><small>Memory used</small><strong>{story.memoryTitle}</strong><p>{story.memorySummary}</p></div></div>
      <div className="mg-story-card__connector" aria-hidden="true" />
      <div className="mg-story-card__step"><span>3</span><div><small>Evidence quote</small><blockquote>{story.evidenceQuote || 'Exact quote was not captured for this older event.'}</blockquote></div></div>
      <div className="mg-story-card__connector" aria-hidden="true" />
      <div className="mg-story-card__step"><span>4</span><div><small>Why MemGuard allowed it</small><strong>{story.roleDescription}</strong><p>{story.whyAllowed}</p></div></div>
      <details className="mg-technical-details">
        <summary>Technical details</summary>
        <dl>
          <div><dt>Memory ID</dt><dd>{item.memory_key}</dd></div>
          <div><dt>Event ID</dt><dd>{item.event_id}</dd></div>
          <div><dt>Content hash</dt><dd>{item.content_hash || 'Unavailable'}</dd></div>
          <div><dt>Recorded</dt><dd>{item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Unavailable'}</dd></div>
        </dl>
      </details>
    </article>
  )
}

export default function EvidenceWorkspace({ trace, inventory }: EvidenceWorkspaceProps) {
  if (!trace) {
    return (
      <main className="mg-workspace mg-workspace--empty">
        <div className="mg-empty-state">
          <p className="mg-eyebrow">No output selected</p>
          <h1>Select an agent output to inspect its evidence story.</h1>
          <p>The memory inventory below remains available even before an output is selected.</p>
        </div>
      </main>
    )
  }

  const evidenceInputs = inputEvidence(trace)
  const missingEvidence = trace.missing_evidence_event_ids || []
  const inventoryById = new Map(inventory.map(memory => [memory.memory_id, memory]))
  const rejected = inventory.filter(memory => memoryUsage(memory, trace) === 'rejected')
  const available = inventory.filter(memory => memoryUsage(memory, trace) === 'available')

  return (
    <main className="mg-workspace">
      <header className="mg-workspace__header">
        <div>
          <p className="mg-eyebrow">Governed answer evidence</p>
          <h1>Why did the agent say this?</h1>
        </div>
        <dl className="mg-trace-meta">
          <div><dt>Agent</dt><dd>{trace.agent_id.replaceAll('_', ' ')}</dd></div>
          <div><dt>Memory used</dt><dd>{evidenceInputs.length}</dd></div>
          <div><dt>Generated</dt><dd>{new Date(trace.timestamp).toLocaleString()}</dd></div>
        </dl>
      </header>

      <p className="mg-truth-note">MemGuard records which governed memory entered the prompt and which claim it supports. It does not claim to expose the model&apos;s hidden reasoning.</p>

      <section className="mg-selected-output" aria-labelledby="mg-selected-output-title">
        <h2 id="mg-selected-output-title">Agent answer</h2>
        <HighlightedAnswer answer={traceOutput(trace)} evidence={evidenceInputs} />
      </section>

      <div className="mg-section-heading">
        <h2>Evidence story</h2>
        <p>Claim → real memory → exact quote → governance decision</p>
      </div>

      <section className="mg-story-list" aria-label="Claim evidence stories">
        {evidenceInputs.length ? evidenceInputs.map(item => (
          <EvidenceStoryCard key={item.event_id} item={item} memory={inventoryById.get(item.memory_key)} />
        )) : <p className="mg-stage-empty">No persisted memory evidence is linked to this output.</p>}
      </section>

      <section className="mg-related-memory" aria-labelledby="mg-related-memory-title">
        <header><div><p className="mg-eyebrow">Decision boundary</p><h2 id="mg-related-memory-title">Other memory the agent could have encountered</h2></div></header>
        <div className="mg-related-memory__columns">
          <article><h3>Rejected by MemGuard <span>{rejected.length}</span></h3>{rejected.map(memory => <div key={memory.memory_id}><strong>{memory.display_name}</strong><p>{memory.summary}</p><small>{memory.policy_explanation}</small></div>)}</article>
          <article><h3>Available, not used <span>{available.length}</span></h3>{available.map(memory => <div key={memory.memory_id}><strong>{memory.display_name}</strong><p>{memory.summary}</p><small>No recorded claim-level link to this answer.</small></div>)}</article>
        </div>
      </section>

      {missingEvidence.length > 0 && (
        <section className="mg-evidence-gap" role="status"><strong>Evidence gap</strong><p>{missingEvidence.length} linked event record{missingEvidence.length === 1 ? ' is' : 's are'} unavailable. MemGuard did not fabricate a replacement.</p></section>
      )}
    </main>
  )
}
