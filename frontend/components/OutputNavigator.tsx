'use client'

import { DecisionTrace, inputEvidence, outputEvidence, traceOutput } from '../lib/dashboard'

interface OutputNavigatorProps {
  traces: DecisionTrace[]
  selectedTraceId: string | null
  onSelect: (traceId: string) => void
  agentFilter: string
  agentList: string[]
  onAgentFilterChange: (agentId: string) => void
}

export default function OutputNavigator({
  traces,
  selectedTraceId,
  onSelect,
  agentFilter,
  agentList,
  onAgentFilterChange,
}: OutputNavigatorProps) {
  return (
    <aside className="mg-output-nav" aria-label="Agent outputs">
      <div className="mg-output-nav__header">
        <p className="mg-eyebrow">Output-first investigation</p>
        <div className="mg-output-nav__title-row">
          <h2>Agent outputs</h2>
          <span>{traces.length}</span>
        </div>
        <label className="mg-field-label" htmlFor="mg-agent-filter">Agent</label>
        <select
          id="mg-agent-filter"
          className="mg-select"
          value={agentFilter}
          onChange={(event) => onAgentFilterChange(event.target.value)}
        >
          <option value="all">All agents</option>
          {agentList.map(agentId => (
            <option key={agentId} value={agentId}>{agentId}</option>
          ))}
        </select>
      </div>

      <div className="mg-output-list">
        {traces.length === 0 ? (
          <div className="mg-output-nav__empty">
            <span>No recorded outputs</span>
            <p>Run an instrumented agent to create an evidence trace.</p>
          </div>
        ) : traces.map(trace => {
          const selected = trace.trace_id === selectedTraceId
          const output = traceOutput(trace)
          return (
            <button
              key={trace.trace_id}
              type="button"
              className={`mg-output-item${selected ? ' is-selected' : ''}`}
              aria-pressed={selected}
              onClick={() => onSelect(trace.trace_id)}
            >
              <span className="mg-output-item__topline">
                <span className="mg-output-item__agent">{trace.agent_id}</span>
                <time dateTime={trace.timestamp}>
                  {new Date(trace.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </time>
              </span>
              <span className="mg-output-item__preview">{output}</span>
              <span className="mg-output-item__meta">
                <span>{inputEvidence(trace).length} evidence</span>
                <span>{outputEvidence(trace).length} writes</span>
                <span>{(trace.total_influence_score || 0).toFixed(2)} rank</span>
              </span>
            </button>
          )
        })}
      </div>
    </aside>
  )
}
