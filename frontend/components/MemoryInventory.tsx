import { DecisionTrace, GovernedMemory, memoryUsage, MemoryUsage } from '../lib/dashboard'

interface MemoryInventoryProps {
  memories: GovernedMemory[]
  trace: DecisionTrace | null
}

const usagePresentation: Record<MemoryUsage, { label: string; description: string }> = {
  used: {
    label: 'Used in this answer',
    description: 'This governed memory entered the prompt and is linked to a claim in the selected answer.',
  },
  constrained: {
    label: 'Constrained this answer',
    description: 'This memory limited what the agent could say or do, even if its content was not quoted.',
  },
  rejected: {
    label: 'Rejected by policy',
    description: 'MemGuard evaluated this memory but kept it out of the agent prompt.',
  },
  available: {
    label: 'Available, not used',
    description: 'This memory is eligible, but no claim-level link to the selected answer was recorded.',
  },
}

function formatSource(memory: GovernedMemory) {
  return memory.source_id ? `${memory.source_type} · ${memory.source_id}` : memory.source_type
}

export default function MemoryInventory({ memories, trace }: MemoryInventoryProps) {
  return (
    <section className="mg-inventory" aria-labelledby="mg-inventory-title">
      <header className="mg-inventory__header">
        <div>
          <p className="mg-eyebrow">Governed memory inventory</p>
          <h2 id="mg-inventory-title">What the agent actually remembers</h2>
          <p>Real records available to this support agent, shown with their current governance decision.</p>
        </div>
        <span>{memories.length} memories</span>
      </header>

      <div className="mg-inventory__list">
        {memories.length === 0 ? (
          <p className="mg-stage-empty">No governed memories are available for this tenant.</p>
        ) : memories.map(memory => {
          const usage = memoryUsage(memory, trace)
          const presentation = usagePresentation[usage]
          const factors = Object.entries(memory.trust_factors || {})
          return (
            <article className={`mg-memory-card mg-memory-card--${usage}`} key={memory.memory_id}>
              <header>
                <div>
                  <span className={`mg-memory-status mg-memory-status--${usage}`}>{presentation.label}</span>
                  <h3>{memory.display_name}</h3>
                </div>
                <strong className="mg-trust-score">
                  {memory.trust_score === null ? 'Not scored' : `${Math.round(memory.trust_score)}% trust`}
                </strong>
              </header>

              <p className="mg-memory-summary">{memory.summary}</p>

              <div className="mg-memory-explanation">
                <h4>{usage === 'used' ? 'Why this memory was used' : 'Why MemGuard made this decision'}</h4>
                <p>{presentation.description}</p>
                <p>{memory.policy_explanation}</p>
              </div>

              <dl className="mg-memory-facts">
                <div><dt>Source</dt><dd>{formatSource(memory)}</dd></div>
                <div><dt>Writer</dt><dd>{memory.writer_id || 'System record'}</dd></div>
                <div><dt>Verified</dt><dd>{memory.verified_at ? new Date(memory.verified_at).toLocaleString() : 'Not recorded'}</dd></div>
                <div><dt>Conflict check</dt><dd>{memory.conflict_status || 'Not recorded'}</dd></div>
              </dl>

              {factors.length > 0 && (
                <div className="mg-trust-factors">
                  <h4>Trust factors</h4>
                  {factors.map(([name, factor]) => (
                    <div key={name}>
                      <span>{name.replaceAll('_', ' ')}</span>
                      <strong>{factor.score === null ? '—' : Math.round(factor.score)}</strong>
                      <p>{factor.reason}</p>
                    </div>
                  ))}
                </div>
              )}

              <details className="mg-technical-details">
                <summary>Technical details</summary>
                <dl>
                  <div><dt>Memory ID</dt><dd>{memory.memory_id}</dd></div>
                  <div><dt>Policy status</dt><dd>{memory.policy_status}</dd></div>
                  <div><dt>Reason codes</dt><dd>{memory.policy_reason_codes?.join(', ') || 'None'}</dd></div>
                </dl>
              </details>
            </article>
          )
        })}
      </div>
    </section>
  )
}
