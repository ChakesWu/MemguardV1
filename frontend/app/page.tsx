'use client'

import { useEffect, useState } from 'react'
import MemoryDiffViewer, { ChangePulse } from '../components/MemoryDiffViewer'
import ConflictWarning from '../components/ConflictWarning'
import AuditReport from '../components/AuditReport'

interface MemoryEvent {
  event_id: string
  agent_id: string
  session_id: string
  operation: string
  memory_key: string
  namespace: string
  memory_type: string
  content_hash: string
  timestamp: string
  context?: Record<string, any>
  before_value?: any
  after_value?: any
}

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

interface Stats {
  total_events: number
  total_decision_traces: number
  db_path: string
}

interface DecisionTrace {
  trace_id: string
  agent_id: string
  session_id: string
  timestamp: string
  total_influence_score: number
  input_memory_ids: string[]
  output_memory_ids: string[]
  input_memory_details?: { agent_id: string; memory_key: string; operation: string }[]
  output_memory_details?: { agent_id: string; memory_key: string; operation: string }[]
  llm_output: string
  user_input: string
  memory_influence_scores?: Record<string, number>
  metadata?: Record<string, any>
  output_summary?: string
}

const FINCOMPLI_AGENTS = [
  'fincompli-supervisor',
  'fraud_detection',
  'case_history',
  'compliance_research',
  'report_generation',
]

function computeChangeCount(before: any, after: any): number {
  if (!before && !after) return 0
  if (!before) return Object.keys(after || {}).length
  if (!after) return Object.keys(before || {}).length
  const allKeys = new Set([...Object.keys(before), ...Object.keys(after)])
  let changes = 0
  allKeys.forEach(k => {
    if (JSON.stringify(before[k]) !== JSON.stringify(after[k])) changes++
  })
  return changes
}

// ── Badge styles ──

const OP_COLORS: Record<string, string> = {
  create: 'bg-green-500',
  read: 'bg-blue-500',
  update: 'bg-yellow-500',
  delete: 'bg-red-500',
  query: 'bg-cyan-500',
  search: 'bg-purple-500',
}

const OP_ICONS: Record<string, string> = {
  create: '🟢',
  read: '🔵',
  update: '🟡',
  delete: '🔴',
  query: '🔷',
  search: '🟣',
}

const MEMTYPE_COLORS: Record<string, string> = {
  episodic: 'bg-blue-700 text-blue-200',
  semantic: 'bg-green-700 text-green-200',
  procedural: 'bg-purple-700 text-purple-200',
  working: 'bg-gray-600 text-gray-200',
}

const MEMTYPE_ICONS: Record<string, string> = {
  episodic: '📖',
  semantic: '📚',
  procedural: '⚙️',
  working: '💾',
}

// ── Render a memory_key with icon based on prefix ──
function memoryKeyLabel(key: string): { icon: string; label: string; colorClass: string } {
  if (key.startsWith('episodic:')) {
    return { icon: '📖', label: key.replace('episodic:', 'SAR '), colorClass: 'text-blue-300' }
  }
  if (key.startsWith('semantic:')) {
    return { icon: '📚', label: key.replace('semantic:', ''), colorClass: 'text-green-300' }
  }
  if (key.startsWith('procedural:')) {
    return { icon: '⚙️', label: key.replace('procedural:', 'SOP '), colorClass: 'text-purple-300' }
  }
  if (key.startsWith('state:')) {
    return { icon: '💾', label: key, colorClass: 'text-yellow-300' }
  }
  if (key.startsWith('checkpoint:')) {
    return { icon: '📌', label: key, colorClass: 'text-gray-400' }
  }
  return { icon: '•', label: key, colorClass: 'text-gray-300' }
}

export default function DashboardPage() {
  const [events, setEvents] = useState<MemoryEvent[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [traces, setTraces] = useState<DecisionTrace[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState<MemoryEvent | null>(null)
  const [selectedTrace, setSelectedTrace] = useState<DecisionTrace | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [agentFilter, setAgentFilter] = useState<string>('all')
  const [conflicts, setConflicts] = useState<Conflict[]>([])
  const [showConflicts, setShowConflicts] = useState(false)
  const [showAudit, setShowAudit] = useState(false)
  const [conflictEventIds, setConflictEventIds] = useState<Set<string>>(new Set())

  const API_BASE = 'http://localhost:8000'

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [filter, agentFilter])

  const fetchData = async () => {
    try {
      const statsRes = await fetch(`${API_BASE}/v1/db/stats`)
      const statsData = await statsRes.json()
      setStats(statsData)

      // Build query params
      const params = new URLSearchParams()
      params.set('limit', '200')
      if (filter !== 'all') params.set('operation', filter)
      if (agentFilter !== 'all') params.set('agent_id', agentFilter)

      const eventsRes = await fetch(`${API_BASE}/v1/events?${params.toString()}`)
      const eventsData = await eventsRes.json()
      setEvents(eventsData.events || [])

      // Fetch decision traces for the selected agent (or all agents for tenant)
      try {
        const traceAgent = agentFilter !== 'all' ? agentFilter : null
        const traceNamespace = 'fincompli'
        let tracesUrl: string
        if (traceAgent) {
          tracesUrl = `${API_BASE}/v1/trace/agent/${traceNamespace}/${traceAgent}`
        } else {
          tracesUrl = `${API_BASE}/v1/trace/tenant/${traceNamespace}`
        }
        const tracesRes = await fetch(tracesUrl)
        const tracesData = await tracesRes.json()
        setTraces(tracesData.traces || [])
      } catch {}

      // Fetch conflicts
      try {
        const conflictsRes = await fetch(`${API_BASE}/v1/analysis/conflicts?window_seconds=10`)
        const conflictsData = await conflictsRes.json()
        setConflicts(conflictsData.conflicts || [])
        const ids = new Set<string>()
        for (const c of (conflictsData.conflicts || [])) {
          ids.add(c.event_a)
          ids.add(c.event_b)
        }
        setConflictEventIds(ids)
      } catch {}

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch data:', error)
      setLoading(false)
    }
  }

  // ── Dynamic agent list from events ──
  const agentList = (() => {
    const seen = new Set<string>()
    events.forEach(e => { if (e.agent_id) seen.add(e.agent_id) })
    // Merge with known fincompli agents
    FINCOMPLI_AGENTS.forEach(a => seen.add(a))
    seen.add('demo-chatbot')
    return Array.from(seen).sort()
  })()

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⏳</div>
          <div className="text-xl">Loading MemGuard Dashboard...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">🔍 MemGuard Dashboard</h1>
              <p className="text-gray-400 text-sm mt-1">Memory Observability for AI Agents</p>
            </div>
            <div className="flex items-center gap-3">
              {conflicts.length > 0 && (
                <button
                  onClick={() => setShowConflicts(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition text-sm"
                  style={{ backgroundColor: '#591d2e', color: '#ff5252' }}
                >
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  {conflicts.length} Conflict{conflicts.length > 1 ? 's' : ''}
                </button>
              )}
              <button
                onClick={() => setShowAudit(true)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition text-sm"
              >
                📄 Audit Report
              </button>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
              >
                🔄 Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="text-2xl font-bold text-blue-400">{stats?.total_events || 0}</div>
            <div className="text-gray-400 text-xs mt-1">Events</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="text-2xl font-bold text-green-400">{events.filter(e => e.operation === 'create').length}</div>
            <div className="text-gray-400 text-xs mt-1">Created</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="text-2xl font-bold text-blue-400">{events.filter(e => e.operation === 'read').length}</div>
            <div className="text-gray-400 text-xs mt-1">Read</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="text-2xl font-bold text-yellow-400">{events.filter(e => e.operation === 'update').length}</div>
            <div className="text-gray-400 text-xs mt-1">Updated</div>
            <div className="mt-1 scale-75 origin-left">
              <ChangePulse count={events.filter(e => e.operation === 'update').length} size={6} />
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="text-2xl font-bold text-purple-400">{traces.length}</div>
            <div className="text-gray-400 text-xs mt-1">Traces</div>
          </div>
        </div>

        {/* Filters — Operation + Agent */}
        <div className="mb-6 flex flex-wrap gap-2 items-center">
          <span className="text-xs text-gray-500 mr-1">Op:</span>
          {['all', 'create', 'read', 'update', 'delete', 'query'].map(op => (
            <button
              key={op}
              onClick={() => setFilter(op)}
              className={`px-3 py-1.5 rounded-lg transition text-xs ${
                filter === op
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {op.toUpperCase()}
            </button>
          ))}
          <span className="ml-4 text-xs text-gray-500 mr-1">Agent:</span>
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 border border-gray-700 text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Agents</option>
            {agentList.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>

        {/* Events Table */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden mb-8">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Op</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Agent</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Memory Key</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {events.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      <div className="text-4xl mb-2">📭</div>
                      <div>No events found</div>
                      <div className="text-sm mt-2">Run the fincompli baseline with MemGuard:</div>
                      <code className="block mt-2 text-xs bg-gray-800 px-4 py-2 rounded mx-auto max-w-lg">
                        cd fincompli-baseline && ./run_with_memguard.sh<br/>
                        Then open http://localhost:3001
                      </code>
                    </td>
                  </tr>
                ) : (
                  events.map(event => {
                    const isConflictEvent = conflictEventIds.has(event.event_id)
                    return (
                    <tr
                      key={event.event_id}
                      className={`hover:bg-gray-800 cursor-pointer transition ${
                        isConflictEvent ? 'bg-red-950/30 border-l-2 border-red-600' : ''
                      }`}
                      onClick={() => setSelectedEvent(event)}
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-400">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${OP_COLORS[event.operation] || 'bg-gray-500'} bg-opacity-20`}>
                          {(OP_ICONS[event.operation] || '⚪')} {event.operation}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-300">
                        {event.agent_id}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-300 font-mono max-w-xs truncate">
                        {event.memory_key}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {event.memory_type && event.memory_type !== 'working' ? (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${MEMTYPE_COLORS[event.memory_type] || 'bg-gray-600 text-gray-300'}`}>
                            {MEMTYPE_ICONS[event.memory_type] || ''} {event.memory_type}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-600">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-500 font-mono">
                        {event.content_hash?.substring(0, 8)}...
                      </td>
                    </tr>
                  )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Decision Traces Section */}
        {traces.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              🧠 Decision Traces
              <span className="text-xs text-gray-500 font-normal">
                (memory IN → agent decision → memory OUT)
              </span>
            </h2>
            <div className="space-y-3">
              {traces.slice(0, 10).map(trace => (
                <div
                  key={trace.trace_id}
                  className="bg-gray-900 rounded-lg border border-gray-800 p-4 hover:border-purple-700 cursor-pointer transition"
                  onClick={() => setSelectedTrace(trace)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-gray-400">
                        {new Date(trace.timestamp).toLocaleTimeString()}
                      </span>
                      <span className="text-xs font-medium text-purple-400">
                        {trace.agent_id}
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                        (trace.total_influence_score || 0) >= 0.7
                          ? 'bg-purple-900 text-purple-200'
                          : (trace.total_influence_score || 0) >= 0.4
                          ? 'bg-blue-900 text-blue-200'
                          : 'bg-gray-700 text-gray-300'
                      }`}>
                        influence: {(trace.total_influence_score || 0).toFixed(2)}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {trace.input_memory_ids?.length || 0} reads → {trace.output_memory_ids?.length || 0} writes
                    </span>
                  </div>
                  {/* Show input memory key previews */}
                  {(trace.input_memory_details || []).length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-1">
                      {(trace.input_memory_details || []).slice(0, 5).map((d, i) => {
                        const mk = memoryKeyLabel(d.memory_key || '')
                        return (
                          <span key={i} className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] bg-blue-950/50 text-blue-300 font-mono">
                            {mk.icon} {mk.label.length > 35 ? mk.label.substring(0,35)+'…' : mk.label}
                          </span>
                        )
                      })}
                      {(trace.input_memory_ids?.length || 0) > 5 && (
                        <span className="text-[10px] text-gray-500">+{(trace.input_memory_ids?.length || 0) - 5} more</span>
                      )}
                    </div>
                  )}
                  {trace.llm_output && (
                    <p className="text-xs text-gray-300 line-clamp-2">
                      {trace.llm_output.substring(0, 200)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Connection Status */}
        <div className="mt-6 text-center text-sm text-gray-500">
          {stats ? (
            <span className="text-green-400">● Connected to backend</span>
          ) : (
            <span className="text-red-400">● Backend not available</span>
          )}
          {' | '}
          <span>DB: {stats?.db_path || 'unknown'}</span>
        </div>
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedEvent(null)}
        >
          <div
            className="bg-[#0d1219] rounded-lg max-w-5xl w-full max-h-[85vh] overflow-y-auto border border-gray-800 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-gray-800 px-6 py-4 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-xl font-bold">Event Details</h3>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-gray-400">Event ID</dt>
                  <dd className="mt-1 text-sm text-gray-200 font-mono">{selectedEvent.event_id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-400">Operation</dt>
                  <dd className="mt-1">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${OP_COLORS[selectedEvent.operation] || 'bg-gray-500'} bg-opacity-20`}>
                      {(OP_ICONS[selectedEvent.operation] || '⚪')} {selectedEvent.operation.toUpperCase()}
                    </span>
                  </dd>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-400">Agent ID</dt>
                    <dd className="mt-1 text-sm text-gray-200">{selectedEvent.agent_id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-400">Session ID</dt>
                    <dd className="mt-1 text-sm text-gray-200">{selectedEvent.session_id}</dd>
                  </div>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-400">Memory Key</dt>
                  <dd className="mt-1 text-sm text-gray-200 font-mono">{selectedEvent.memory_key}</dd>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-400">Namespace</dt>
                    <dd className="mt-1 text-sm text-gray-200">{selectedEvent.namespace}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-400">Memory Type</dt>
                    <dd className="mt-1">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${MEMTYPE_COLORS[selectedEvent.memory_type] || 'bg-gray-600 text-gray-300'}`}>
                        {MEMTYPE_ICONS[selectedEvent.memory_type] || ''} {selectedEvent.memory_type}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-400">Content Hash</dt>
                    <dd className="mt-1 text-sm text-gray-200 font-mono">{selectedEvent.content_hash}</dd>
                  </div>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-400">Timestamp</dt>
                  <dd className="mt-1 text-sm text-gray-200">{new Date(selectedEvent.timestamp).toLocaleString()}</dd>
                </div>
                {selectedEvent.context && Object.keys(selectedEvent.context).length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-400">Context</dt>
                    <dd className="mt-1 text-sm text-gray-200">
                      <pre className="bg-gray-800 p-3 rounded text-xs overflow-x-auto">
                        {JSON.stringify(selectedEvent.context, null, 2)}
                      </pre>
                    </dd>
                  </div>
                )}
                {(selectedEvent.before_value || selectedEvent.after_value) && (
                  <div>
                    <dt className="text-sm font-medium text-gray-400 mb-2">State Diff</dt>
                    <dd>
                      <MemoryDiffViewer
                        before={selectedEvent.before_value}
                        after={selectedEvent.after_value}
                      />
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        </div>
      )}

      {/* DecisionTrace Detail Panel */}
      {selectedTrace && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedTrace(null)}
        >
          <div
            className="bg-[#0d1219] rounded-lg max-w-4xl w-full max-h-[85vh] overflow-y-auto border border-purple-800 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-purple-900 px-6 py-4 border-b border-purple-700 flex items-center justify-between">
              <h3 className="text-xl font-bold flex items-center gap-2">
                🧠 Decision Trace
              </h3>
              <button
                onClick={() => setSelectedTrace(null)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            <div className="p-6 space-y-6">
              {/* ── Memory IN ── */}
              <div>
                <h4 className="text-sm font-bold text-blue-400 mb-2 flex items-center gap-2">
                  📥 Memory IN <span className="text-xs text-gray-500 font-normal">(Agent 讀了這些記憶之後才做決策)</span>
                </h4>
                <div className="bg-blue-950/30 border border-blue-900 rounded-lg p-3">
                  {(selectedTrace.input_memory_details?.length || selectedTrace.input_memory_ids?.length || 0) > 0 ? (
                    <ul className="space-y-2">
                      {(selectedTrace.input_memory_details || selectedTrace.input_memory_ids.map(id => ({ memory_key: id.substring(0,12)+'...', agent_id: '?', operation: '?' }))).map((detail, i) => {
                        const mk = memoryKeyLabel(detail.memory_key || '')
                        return (
                          <li key={i} className="flex items-start gap-2 text-xs">
                            <span className="mt-0.5">{mk.icon}</span>
                            <div>
                              <span className={`font-mono ${mk.colorClass}`}>{mk.label}</span>
                              <span className="text-gray-500 ml-2">← {detail.operation}</span>
                            </div>
                          </li>
                        )
                      })}
                    </ul>
                  ) : (
                    <p className="text-xs text-gray-500">沒有讀取任何記憶 (純 LLM 推理)</p>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  這些記憶影響了 Agent 的決策
                  {selectedTrace.total_influence_score > 0.6 ? ' — 高度依賴記憶' : selectedTrace.total_influence_score > 0.3 ? ' — 中度依賴記憶' : ''}
                </p>
              </div>

              {/* ── Agent Decision ── */}
              <div>
                <h4 className="text-sm font-bold text-purple-400 mb-2 flex items-center gap-2">
                  🤖 Agent Decision
                  <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
                    (selectedTrace.total_influence_score || 0) >= 0.7
                      ? 'bg-purple-900 text-purple-200'
                      : 'bg-blue-900 text-blue-200'
                  }`}>
                    Influence: {(selectedTrace.total_influence_score || 0).toFixed(2)}
                  </span>
                </h4>
                <div className="bg-purple-950/30 border border-purple-900 rounded-lg p-3">
                  <div className="text-xs text-gray-400 mb-1">
                    Agent: <span className="text-purple-300">{selectedTrace.agent_id}</span>
                    {' · '}
                    Session: <span className="text-purple-300 font-mono">{selectedTrace.session_id}</span>
                  </div>
                  {selectedTrace.llm_output ? (
                    <pre className="text-xs text-gray-200 whitespace-pre-wrap mt-2 bg-black/30 p-3 rounded max-h-64 overflow-y-auto">
                      {selectedTrace.llm_output}
                    </pre>
                  ) : selectedTrace.user_input ? (
                    <p className="text-xs text-gray-300 mt-2">{selectedTrace.user_input}</p>
                  ) : (
                    <p className="text-xs text-gray-500">No output recorded</p>
                  )}
                </div>
              </div>

              {/* ── Memory OUT ── */}
              <div>
                <h4 className="text-sm font-bold text-green-400 mb-2 flex items-center gap-2">
                  📤 Memory OUT <span className="text-xs text-gray-500 font-normal">(Agent 做了這個決策後寫入了什麼)</span>
                </h4>
                <div className="bg-green-950/30 border border-green-900 rounded-lg p-3">
                  {(selectedTrace.output_memory_details?.length || selectedTrace.output_memory_ids?.length || 0) > 0 ? (
                    <ul className="space-y-2">
                      {(selectedTrace.output_memory_details || selectedTrace.output_memory_ids.map(id => ({ memory_key: id.substring(0,12)+'...', agent_id: '?', operation: 'create' }))).map((detail, i) => {
                        const mk = memoryKeyLabel(detail.memory_key || '')
                        return (
                          <li key={i} className="flex items-start gap-2 text-xs">
                            <span className="mt-0.5">{mk.icon}</span>
                            <div>
                              <span className={`font-mono ${mk.colorClass}`}>{mk.label}</span>
                              <span className="text-gray-500 ml-2">→ {detail.operation || 'write'}</span>
                            </div>
                          </li>
                        )
                      })}
                    </ul>
                  ) : (
                    <p className="text-xs text-gray-500">沒有寫入新記憶</p>
                  )}
                </div>
              </div>

              {/* ── Trace metadata ── */}
              {selectedTrace.metadata && Object.keys(selectedTrace.metadata).length > 0 && (
                <div>
                  <h4 className="text-sm font-bold text-gray-400 mb-2">Metadata</h4>
                  <pre className="bg-gray-800 p-3 rounded text-xs text-gray-300 overflow-x-auto">
                    {JSON.stringify(selectedTrace.metadata, null, 2)}
                  </pre>
                </div>
              )}

              <div className="text-xs text-gray-500">
                Trace ID: <span className="font-mono">{selectedTrace.trace_id}</span>
                {' · '}
                {new Date(selectedTrace.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Conflict Warning Panel */}
      {showConflicts && (
        <ConflictWarning conflicts={conflicts} onClose={() => setShowConflicts(false)} />
      )}

      {/* Audit Report Panel */}
      {showAudit && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-end p-0 z-50 backdrop-blur-sm"
          onClick={() => setShowAudit(false)}>
          <div className="bg-[#0d1219] border-l border-gray-800 max-w-2xl w-full h-full overflow-y-auto shadow-2xl"
            onClick={e => e.stopPropagation()}>
            <AuditReport onClose={() => setShowAudit(false)} />
          </div>
        </div>
      )}
    </div>
  )
}
