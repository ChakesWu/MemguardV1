'use client'

interface Conflict {
  memory_key: string
  agent_a: string
  agent_b: string
  delta_seconds: number
  severity: 'critical' | 'high' | 'medium'
  same_content: boolean
  time_a: string
  time_b: string
  event_a: string
  event_b: string
}

function conflictDistance(conflict: Conflict): string {
  return conflict.delta_seconds < 1
    ? `${(conflict.delta_seconds * 1000).toFixed(0)} ms apart`
    : `${conflict.delta_seconds.toFixed(1)} s apart`
}

export default function ConflictWarning({
  conflicts,
  onClose,
}: {
  conflicts: Conflict[]
  onClose: () => void
}) {
  const critical = conflicts.filter(conflict => conflict.severity === 'critical').length
  const high = conflicts.filter(conflict => conflict.severity === 'high').length

  return (
    <div className="mg-overlay mg-overlay--side" onClick={onClose}>
      <section className="mg-conflicts" role="dialog" aria-modal="true" aria-labelledby="mg-conflicts-title" onClick={event => event.stopPropagation()}>
        <header className="mg-conflicts__header">
          <div>
            <p className="mg-eyebrow">Memory integrity</p>
            <h2 id="mg-conflicts-title">Conflicts detected</h2>
            <p>{conflicts.length} concurrent write{conflicts.length === 1 ? '' : 's'} to the same memory</p>
          </div>
          <div className="mg-conflicts__actions">
            {critical > 0 && <span className="mg-severity mg-severity--critical">{critical} critical</span>}
            {high > 0 && <span className="mg-severity mg-severity--high">{high} high</span>}
            <button type="button" className="mg-icon-button" aria-label="Close conflicts" onClick={onClose}>×</button>
          </div>
        </header>

        <div className="mg-conflicts__list">
          {conflicts.length === 0 ? (
            <p className="mg-conflicts__empty">No conflicting memory writes are currently recorded.</p>
          ) : conflicts.map((conflict, index) => (
            <article key={`${conflict.event_a}-${conflict.event_b}`} className="mg-conflict">
              <header>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <span className={`mg-severity mg-severity--${conflict.severity}`}>{conflict.severity}</span>
                <time>{conflictDistance(conflict)}</time>
                <span>{conflict.same_content ? 'Identical content' : 'Content differs'}</span>
              </header>
              <code>{conflict.memory_key}</code>
              <div className="mg-conflict__agents">
                <div><span>Agent A</span><strong>{conflict.agent_a}</strong><time>{new Date(conflict.time_a).toLocaleTimeString()}</time></div>
                <div><span>Agent B</span><strong>{conflict.agent_b}</strong><time>{new Date(conflict.time_b).toLocaleTimeString()}</time></div>
              </div>
            </article>
          ))}
        </div>

        <footer className="mg-conflicts__footer">
          Review non-identical concurrent writes and consider a distributed lock or version check for this memory path.
        </footer>
      </section>
    </div>
  )
}
