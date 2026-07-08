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

// ── Severity Badge ─────────────────────────────────────────────────

function SeverityBadge({ severity }: { severity: string }) {
  const colors = {
    critical: { bg: '#591d2e', text: '#ff5252', label: 'CRITICAL' },
    high: { bg: '#3d1a0e', text: '#ff9800', label: 'HIGH' },
    medium: { bg: '#1a2a3d', text: '#ffb74d', label: 'MEDIUM' },
  }
  const c = colors[severity as keyof typeof colors] || colors.medium
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase"
      style={{ backgroundColor: c.bg, color: c.text }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: c.text }}
      />
      {c.label}
    </span>
  )
}

// ── Conflict Card ──────────────────────────────────────────────────

function ConflictCard({ conflict, index }: { conflict: Conflict; index: number }) {
  const timeA = new Date(conflict.time_a).toLocaleTimeString()
  const timeB = new Date(conflict.time_b).toLocaleTimeString()

  return (
    <div
      className="border-b border-gray-800/60 py-4 px-2 hover:bg-[#0d1219] transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-gray-600 text-xs font-mono w-5">{index + 1}</span>
          <SeverityBadge severity={conflict.severity} />
          <span className="text-gray-500 text-xs">
            {conflict.delta_seconds < 1
              ? `${(conflict.delta_seconds * 1000).toFixed(0)}ms apart`
              : `${conflict.delta_seconds.toFixed(1)}s apart`}
          </span>
          {conflict.same_content ? (
            <span className="text-[10px] text-green-500/70 px-1.5 py-0.5 rounded bg-green-500/10">
              identical content
            </span>
          ) : (
            <span className="text-[10px] text-amber-500/70 px-1.5 py-0.5 rounded bg-amber-500/10">
              content differs
            </span>
          )}
        </div>
      </div>

      <div className="font-mono text-xs overflow-x-auto">
        <div className="text-gray-500 mb-1 truncate">
          memory: {conflict.memory_key}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: '#ef5350' }}
            />
            <span className="text-gray-300">{conflict.agent_a}</span>
            <span className="text-gray-600">{timeA}</span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: '#ff9800' }}
            />
            <span className="text-gray-300">{conflict.agent_b}</span>
            <span className="text-gray-600">{timeB}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────────

export default function ConflictWarning({
  conflicts,
  onClose,
}: {
  conflicts: Conflict[]
  onClose: () => void
}) {
  if (conflicts.length === 0) {
    return (
      <div
        className="fixed bottom-6 right-6 bg-[#0d1219] border border-gray-800 rounded-lg shadow-2xl p-4 z-50 animate-in slide-in-from-right-4 max-w-sm"
      >
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-green-400">✓ No conflicts</span>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300">×</button>
        </div>
        <p className="text-xs text-gray-500">
          All memory writes are consistent across agents
        </p>
      </div>
    )
  }

  const critical = conflicts.filter(c => c.severity === 'critical').length
  const high = conflicts.filter(c => c.severity === 'high').length

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-start justify-end p-6 z-50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-[#0d1219] border border-gray-800 rounded-lg shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-[#111820] px-5 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold">Conflicts Detected</h3>
              {critical > 0 && (
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase"
                  style={{ backgroundColor: '#591d2e', color: '#ff5252' }}
                >
                  {critical} critical
                </span>
              )}
              {high > 0 && (
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase"
                  style={{ backgroundColor: '#3d1a0e', color: '#ff9800' }}
                >
                  {high} high
                </span>
              )}
            </div>
            <p className="text-gray-500 text-xs mt-1">
              {conflicts.length} concurrent write{conflicts.length > 1 ? 's' : ''} to the same memory
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 text-xl"
          >
            ×
          </button>
        </div>

        {/* Conflict List */}
        <div className="divide-y divide-gray-800/40">
          {conflicts.map((c, i) => (
            <ConflictCard key={`${c.event_a}-${c.event_b}`} conflict={c} index={i} />
          ))}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-gray-800 bg-[#0a0e15]">
          <p className="text-[11px] text-gray-500 leading-relaxed">
            Multiple agents wrote to the same memory key within the detection window.
            {conflicts.some(c => !c.same_content) &&
              ' Non-identical content may indicate a race condition.'}
            {' '}Review and consider adding a distributed lock or version check.
          </p>
        </div>
      </div>
    </div>
  )
}
