'use client'

import { useState } from 'react'

interface AuditReportData {
  report_id: string
  session_id: string
  generated_at: string
  style: string
  summary: string
  timeline: string[]
  findings: { type: string; severity: string; description: string; recommendation?: string }[]
  recommendations: string[]
  metadata: { total_events: number; agents: string[]; operations: Record<string,number>; duration_seconds: number; conflicts: number }
}

export default function AuditReport({ onClose }: { onClose: () => void }) {
  const [report, setReport] = useState<AuditReportData | null>(null)
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [style, setStyle] = useState('compliance')
  const [sessions, setSessions] = useState<string[]>([])
  const [sessionsLoaded, setSessionsLoaded] = useState(false)

  // 动态获取 session 列表
  if (!sessionsLoaded) {
    setSessionsLoaded(true)
    fetch('http://localhost:8000/v1/events?limit=500')
      .then(r => r.json())
      .then(data => {
        const ids = new Set<string>()
        for (const e of (data.events || [])) {
          const memKey = e.memory_key || ''
          // 从 memory_key 提取 session: checkpoint:SESSION_ID 或 writes:SESSION_ID:xxx
          const match = memKey.match(/^(?:checkpoint|writes):([^:]+)/)
          if (match) ids.add(match[1])
        }
        setSessions([...ids].sort().reverse())
      })
      .catch(() => {})
  }

  const generateReport = async (sid: string) => {
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:8000/v1/analysis/audit/${sid}?style=${style}&format=json`)
      const data = await res.json()
      setReport(data)
    } catch { /* best effort */ }
    setLoading(false)
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Generator */}
      <div className="bg-[#0d1219] rounded-lg border border-gray-800 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Generate Audit Report</h2>
        <div className="flex flex-wrap gap-3">
          <select
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 min-w-[200px]"
          >
            <option value="">Select session...</option>
            {sessions.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <select
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200"
          >
            <option value="compliance">Compliance</option>
            <option value="debug">Debug</option>
            <option value="business">Business</option>
          </select>

          <button
            onClick={() => sessionId && generateReport(sessionId)}
            disabled={!sessionId || loading}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg transition text-sm font-medium"
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Report */}
      {report && (
        <div className="bg-[#0d1219] rounded-lg border border-gray-800 overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-800 bg-[#111820]">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <span className="text-2xl">📄</span>
                  Audit Report
                </h3>
                <p className="text-gray-500 text-xs mt-1">
                  {report?.report_id} · {report?.style?.toUpperCase()} style
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const blob = new Blob(
                      [`# Audit Report\n\n${report.summary}\n\n## Timeline\n${report.timeline.map(t => `- ${t}`).join('\n')}`],
                      { type: 'text/markdown' }
                    )
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url; a.download = `${report.report_id}.md`; a.click()
                  }}
                  className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-xs transition"
                >
                  Export MD
                </button>
                <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Summary */}
            <div>
              <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">Summary</h4>
              <p className="text-gray-200 text-sm leading-relaxed">{report?.summary}</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-5 gap-3">
              {[
                { label: 'Events', value: report.metadata?.total_events ?? 0, color: 'text-blue-400' },
                { label: 'Creates', value: report.metadata?.operations?.create ?? 0, color: 'text-green-400' },
                { label: 'Reads', value: report.metadata?.operations?.read ?? 0, color: 'text-blue-400' },
                { label: 'Updates', value: report.metadata?.operations?.update ?? 0, color: 'text-yellow-400' },
                { label: 'Conflicts', value: report.metadata?.conflicts ?? 0, color: (report.metadata?.conflicts ?? 0) > 0 ? 'text-red-400' : 'text-green-400' },
              ].map(s => (
                <div key={s.label} className="bg-gray-800/50 rounded p-3 text-center">
                  <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Timeline */}
            <div>
              <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">
                Timeline ({report.timeline.length} events)
              </h4>
              <div className="max-h-48 overflow-y-auto space-y-1 font-mono text-xs text-gray-400">
                {report.timeline.slice(0, 15).map((t, i) => (
                  <div key={i} className="hover:text-gray-200 transition">{t}</div>
                ))}
                {report.timeline.length > 15 && (
                  <div className="text-gray-600">... {report.timeline.length - 15} more events</div>
                )}
              </div>
            </div>

            {/* Findings */}
            {report.findings.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">
                  Findings ({report.findings.length})
                </h4>
                <div className="space-y-2">
                  {report.findings.map((f, i) => (
                    <div key={i} className="border border-gray-800 rounded p-4">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          f.severity === 'critical' ? 'bg-red-900/50 text-red-400' :
                          f.severity === 'high' ? 'bg-orange-900/50 text-orange-400' :
                          'bg-yellow-900/50 text-yellow-400'
                        }`}>{f.severity}</span>
                        <span className="text-xs text-gray-400">{f.type}</span>
                      </div>
                      <p className="text-sm text-gray-300">{f.description}</p>
                      {f.recommendation && (
                        <p className="text-xs text-gray-500 mt-1.5">💡 {f.recommendation}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {report.recommendations.length > 0 && (
              <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700/50">
                <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {report.recommendations.map((r, i) => (
                    <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-green-400 mt-0.5">✓</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
