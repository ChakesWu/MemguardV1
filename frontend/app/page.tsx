'use client'

import { useEffect, useState } from 'react'
import AuditReport from '../components/AuditReport'
import ConflictWarning from '../components/ConflictWarning'
import EvidenceWorkspace from '../components/EvidenceWorkspace'
import MemoryDiffViewer from '../components/MemoryDiffViewer'
import OutputNavigator from '../components/OutputNavigator'
import { currentTenantId, loginRequired, logout } from '../lib/auth'
import { Conflict, DecisionTrace, MemoryEvent, Stats } from '../lib/dashboard'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const OPERATIONS = ['all', 'create', 'read', 'update', 'delete', 'query']

export default function DashboardPage() {
  const [events, setEvents] = useState<MemoryEvent[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [traces, setTraces] = useState<DecisionTrace[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState<MemoryEvent | null>(null)
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null)
  const [filter, setFilter] = useState('all')
  const [agentFilter, setAgentFilter] = useState('all')
  const [conflicts, setConflicts] = useState<Conflict[]>([])
  const [showConflicts, setShowConflicts] = useState(false)
  const [showAudit, setShowAudit] = useState(false)
  const [conflictEventIds, setConflictEventIds] = useState<Set<string>>(new Set())
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [authError, setAuthError] = useState<string | null>(null)

  useEffect(() => {
    loginRequired()
      .then(setAccessToken)
      .catch((error) => {
        console.error('Keycloak login failed:', error)
        setAuthError('Unable to sign in with Keycloak. Check that the local identity service is running.')
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!accessToken) return
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [accessToken, filter, agentFilter])

  const apiFetch = (path: string) => fetch(path, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })

  const fetchData = async () => {
    try {
      const statsRes = await apiFetch(`${API_BASE}/v1/db/stats`)
      setStats(await statsRes.json())

      const params = new URLSearchParams({ limit: '200' })
      if (filter !== 'all') params.set('operation', filter)
      if (agentFilter !== 'all') params.set('agent_id', agentFilter)

      const eventsRes = await apiFetch(`${API_BASE}/v1/events?${params.toString()}`)
      const eventsData = await eventsRes.json()
      setEvents(eventsData.events || [])

      try {
        const traceNamespace = currentTenantId()
        if (!traceNamespace) throw new Error('Tenant claim missing from access token')
        const tracesUrl = agentFilter !== 'all'
          ? `${API_BASE}/v1/trace/agent/${traceNamespace}/${agentFilter}`
          : `${API_BASE}/v1/trace/tenant/${traceNamespace}`
        const tracesRes = await apiFetch(tracesUrl)
        const tracesData = await tracesRes.json()
        const nextTraces: DecisionTrace[] = Array.isArray(tracesData)
          ? tracesData
          : tracesData.traces || []
        setTraces(nextTraces)
        setSelectedTraceId(currentId => {
          if (currentId && nextTraces.some(trace => trace.trace_id === currentId)) return currentId
          return nextTraces[0]?.trace_id || null
        })
      } catch (error) {
        console.error('Failed to fetch traces:', error)
      }

      try {
        const conflictsRes = await apiFetch(`${API_BASE}/v1/analysis/conflicts?window_seconds=10`)
        const conflictsData = await conflictsRes.json()
        const nextConflicts: Conflict[] = conflictsData.conflicts || []
        setConflicts(nextConflicts)
        const ids = new Set<string>()
        nextConflicts.forEach(conflict => {
          ids.add(conflict.event_a)
          ids.add(conflict.event_b)
        })
        setConflictEventIds(ids)
      } catch (error) {
        console.error('Failed to fetch conflicts:', error)
      }

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      setLoading(false)
    }
  }

  const agentList = Array.from(new Set([
    ...events.map(event => event.agent_id),
    ...traces.map(trace => trace.agent_id),
  ].filter(Boolean))).sort()
  const selectedTrace = traces.find(trace => trace.trace_id === selectedTraceId) || traces[0] || null

  if (authError) {
    return (
      <div className="mg-state-screen">
        <p className="mg-eyebrow">MemGuard / Authentication</p>
        <h1>Sign-in unavailable</h1>
        <p>{authError}</p>
      </div>
    )
  }

  if (loading && !stats) {
    return (
      <div className="mg-state-screen">
        <p className="mg-eyebrow">MemGuard / Evidence console</p>
        <h1>Loading recorded evidence</h1>
        <span className="mg-loading-line" aria-label="Loading" />
      </div>
    )
  }

  return (
    <div className="mg-app">
      <header className="mg-topbar">
        <div className="mg-brand">
          <span className="mg-wordmark">MEMGUARD</span>
          <span className="mg-product-label">EVIDENCE CONSOLE</span>
        </div>
        <div className="mg-topbar__actions">
          <span className={`mg-connection${stats ? ' is-connected' : ''}`}>
            {stats ? `Connected · ${stats.database_driver || stats.db_path || 'database'}` : 'Backend unavailable'}
          </span>
          <a className="mg-button" href="/agent">Support agent</a>
          {conflicts.length > 0 && (
            <button type="button" className="mg-button mg-button--warning" onClick={() => setShowConflicts(true)}>
              {conflicts.length} conflict{conflicts.length === 1 ? '' : 's'}
            </button>
          )}
          <button type="button" className="mg-button" onClick={() => setShowAudit(true)}>Audit report</button>
          <button type="button" className="mg-button" onClick={fetchData}>Refresh</button>
          <button type="button" className="mg-button mg-button--primary" onClick={() => logout()}>Sign out</button>
        </div>
      </header>

      <div className="mg-dashboard-shell">
        <OutputNavigator
          traces={traces}
          selectedTraceId={selectedTrace?.trace_id || null}
          onSelect={setSelectedTraceId}
          agentFilter={agentFilter}
          agentList={agentList}
          onAgentFilterChange={setAgentFilter}
        />

        <div className="mg-main-column">
          <EvidenceWorkspace trace={selectedTrace} />

          <section className="mg-events" aria-labelledby="mg-events-title">
            <header className="mg-events__header">
              <div>
                <p className="mg-eyebrow">Memory activity</p>
                <h2 id="mg-events-title">Related memory events</h2>
              </div>
              <div className="mg-events__counts">
                <span>{stats?.total_events || 0} total events</span>
                <span>{traces.length} visible outputs</span>
              </div>
            </header>

            <div className="mg-operation-filter" aria-label="Filter memory events">
              {OPERATIONS.map(operation => (
                <button
                  key={operation}
                  type="button"
                  aria-pressed={filter === operation}
                  className={filter === operation ? 'is-active' : ''}
                  onClick={() => setFilter(operation)}
                >
                  {operation}
                </button>
              ))}
            </div>

            <div className="mg-table-wrap">
              <table className="mg-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Operation</th>
                    <th>Agent</th>
                    <th>Memory key</th>
                    <th>Type</th>
                    <th>Content hash</th>
                  </tr>
                </thead>
                <tbody>
                  {events.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="mg-table__empty">No memory events match the current filters.</td>
                    </tr>
                  ) : events.map(event => (
                    <tr
                      key={event.event_id}
                      className={conflictEventIds.has(event.event_id) ? 'has-conflict' : ''}
                      onClick={() => setSelectedEvent(event)}
                    >
                      <td><time dateTime={event.timestamp}>{new Date(event.timestamp).toLocaleTimeString()}</time></td>
                      <td><span className={`mg-operation mg-operation--${event.operation}`}>{event.operation}</span></td>
                      <td>{event.agent_id}</td>
                      <td><code>{event.memory_key}</code></td>
                      <td>{event.memory_type || '—'}</td>
                      <td><code>{event.content_hash ? `${event.content_hash.slice(0, 12)}…` : '—'}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>

      {selectedEvent && (
        <div className="mg-overlay" onClick={() => setSelectedEvent(null)}>
          <section className="mg-modal" role="dialog" aria-modal="true" aria-labelledby="mg-event-title" onClick={event => event.stopPropagation()}>
            <header className="mg-modal__header">
              <div>
                <p className="mg-eyebrow">Memory event</p>
                <h2 id="mg-event-title">Event details</h2>
              </div>
              <button type="button" className="mg-icon-button" aria-label="Close event details" onClick={() => setSelectedEvent(null)}>×</button>
            </header>
            <div className="mg-modal__body">
              <dl className="mg-detail-grid">
                <div className="mg-detail-grid__wide"><dt>Event ID</dt><dd><code>{selectedEvent.event_id}</code></dd></div>
                <div><dt>Operation</dt><dd><span className={`mg-operation mg-operation--${selectedEvent.operation}`}>{selectedEvent.operation}</span></dd></div>
                <div><dt>Memory type</dt><dd>{selectedEvent.memory_type || '—'}</dd></div>
                <div><dt>Agent ID</dt><dd>{selectedEvent.agent_id}</dd></div>
                <div><dt>Session ID</dt><dd><code>{selectedEvent.session_id}</code></dd></div>
                <div className="mg-detail-grid__wide"><dt>Memory key</dt><dd><code>{selectedEvent.memory_key}</code></dd></div>
                <div><dt>Namespace</dt><dd>{selectedEvent.namespace}</dd></div>
                <div><dt>Timestamp</dt><dd>{new Date(selectedEvent.timestamp).toLocaleString()}</dd></div>
                <div className="mg-detail-grid__wide"><dt>Content hash</dt><dd><code>{selectedEvent.content_hash}</code></dd></div>
              </dl>

              {selectedEvent.context && Object.keys(selectedEvent.context).length > 0 && (
                <section className="mg-modal-section">
                  <h3>Recorded context</h3>
                  <pre>{JSON.stringify(selectedEvent.context, null, 2)}</pre>
                </section>
              )}

              {(selectedEvent.before_value || selectedEvent.after_value) && (
                <section className="mg-modal-section">
                  <h3>State diff</h3>
                  <MemoryDiffViewer before={selectedEvent.before_value} after={selectedEvent.after_value} />
                </section>
              )}
            </div>
          </section>
        </div>
      )}

      {showConflicts && <ConflictWarning conflicts={conflicts} onClose={() => setShowConflicts(false)} />}

      {showAudit && (
        <div className="mg-overlay mg-overlay--drawer" onClick={() => setShowAudit(false)}>
          <aside className="mg-drawer" aria-label="Audit report" onClick={event => event.stopPropagation()}>
            {accessToken && <AuditReport accessToken={accessToken} onClose={() => setShowAudit(false)} />}
          </aside>
        </div>
      )}
    </div>
  )
}
