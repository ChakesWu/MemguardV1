'use client'

import { useEffect, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AuditReportData {
  report_id: string
  session_id: string
  generated_at: string
  style: string
  summary: string
  timeline: string[]
  findings: { type: string; severity: string; description: string; recommendation?: string }[]
  recommendations: string[]
  metadata: {
    total_events: number
    agents: string[]
    operations: Record<string, number>
    duration_seconds: number
    conflicts: number
  }
}

interface AuditReportProps {
  accessToken: string
  onClose: () => void
}

export default function AuditReport({ accessToken, onClose }: AuditReportProps) {
  const [report, setReport] = useState<AuditReportData | null>(null)
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [style, setStyle] = useState('compliance')
  const [sessions, setSessions] = useState<string[]>([])

  useEffect(() => {
    let active = true
    fetch(`${API_BASE}/v1/events?limit=500`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then(response => response.json())
      .then(data => {
        if (!active) return
        const ids = new Set<string>()
        for (const event of data.events || []) {
          if (event.session_id) ids.add(event.session_id)
        }
        setSessions([...ids].sort().reverse())
      })
      .catch(() => {})

    return () => { active = false }
  }, [accessToken])

  const generateReport = async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/v1/analysis/audit/${sessionId}?style=${style}&format=json`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      setReport(await response.json())
    } catch {
      setReport(null)
    } finally {
      setLoading(false)
    }
  }

  const exportMarkdown = () => {
    if (!report) return
    const blob = new Blob(
      [`# Audit Report\n\n${report.summary}\n\n## Timeline\n${report.timeline.map(item => `- ${item}`).join('\n')}`],
      { type: 'text/markdown' },
    )
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${report.report_id}.md`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mg-audit">
      <header className="mg-audit__header">
        <div>
          <p className="mg-eyebrow">Evidence export</p>
          <h2>Audit report</h2>
        </div>
        <button type="button" className="mg-icon-button" aria-label="Close audit report" onClick={onClose}>×</button>
      </header>

      <div className="mg-audit__body">
        <section className="mg-audit__generator">
          <label htmlFor="mg-audit-session">Session</label>
          <select id="mg-audit-session" value={sessionId} onChange={event => setSessionId(event.target.value)}>
            <option value="">Select recorded session</option>
            {sessions.map(session => <option key={session} value={session}>{session}</option>)}
          </select>

          <label htmlFor="mg-audit-style">Report style</label>
          <select id="mg-audit-style" value={style} onChange={event => setStyle(event.target.value)}>
            <option value="compliance">Compliance</option>
            <option value="debug">Debug</option>
            <option value="business">Business</option>
          </select>

          <button type="button" className="mg-button mg-button--primary" disabled={!sessionId || loading} onClick={generateReport}>
            {loading ? 'Generating' : 'Generate report'}
          </button>
        </section>

        {report && (
          <article className="mg-audit__report">
            <header className="mg-audit__report-header">
              <div>
                <p className="mg-eyebrow">{report.style} / {report.report_id}</p>
                <h3>Recorded session evidence</h3>
              </div>
              <button type="button" className="mg-button" onClick={exportMarkdown}>Export MD</button>
            </header>

            <section className="mg-audit__section">
              <h4>Summary</h4>
              <p>{report.summary}</p>
            </section>

            <dl className="mg-audit__stats">
              <div><dt>Events</dt><dd>{report.metadata.total_events}</dd></div>
              <div><dt>Creates</dt><dd>{report.metadata.operations.create || 0}</dd></div>
              <div><dt>Reads</dt><dd>{report.metadata.operations.read || 0}</dd></div>
              <div><dt>Updates</dt><dd>{report.metadata.operations.update || 0}</dd></div>
              <div><dt>Conflicts</dt><dd>{report.metadata.conflicts}</dd></div>
            </dl>

            <section className="mg-audit__section">
              <h4>Timeline · {report.timeline.length} events</h4>
              <ol className="mg-audit__timeline">
                {report.timeline.slice(0, 15).map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
              </ol>
            </section>

            {report.findings.length > 0 && (
              <section className="mg-audit__section">
                <h4>Findings · {report.findings.length}</h4>
                <div className="mg-audit__findings">
                  {report.findings.map((finding, index) => (
                    <article key={`${finding.type}-${index}`}>
                      <div><span className={`mg-severity mg-severity--${finding.severity}`}>{finding.severity}</span><span>{finding.type}</span></div>
                      <p>{finding.description}</p>
                      {finding.recommendation && <small>{finding.recommendation}</small>}
                    </article>
                  ))}
                </div>
              </section>
            )}

            {report.recommendations.length > 0 && (
              <section className="mg-audit__section">
                <h4>Recommendations</h4>
                <ul className="mg-audit__recommendations">
                  {report.recommendations.map((recommendation, index) => <li key={`${index}-${recommendation}`}>{recommendation}</li>)}
                </ul>
              </section>
            )}
          </article>
        )}
      </div>
    </div>
  )
}
