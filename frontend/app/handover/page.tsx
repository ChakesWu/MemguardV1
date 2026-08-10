'use client'

import { useEffect, useState } from 'react'

import EnterpriseHandoverDemo from '../../components/EnterpriseHandoverDemo'
import { loginRequired, logout } from '../../lib/auth'
import { EnterpriseHandoverReport } from '../../lib/handover'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function EnterpriseHandoverPage() {
  const [report, setReport] = useState<EnterpriseHandoverReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loginRequired()
      .then(async token => {
        const response = await fetch(`${API_BASE}/v1/demo/enterprise-handover`, { headers: { Authorization: `Bearer ${token}` } })
        if (!response.ok) throw new Error('The enterprise handover demo could not be loaded.')
        setReport(await response.json())
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : 'Unable to load the demo.'))
  }, [])

  if (error) return <main className="mg-state-screen"><p className="mg-eyebrow">MemGuard / Enterprise handover</p><h1>Demo unavailable</h1><p>{error}</p></main>
  if (!report) return <main className="mg-state-screen"><p className="mg-eyebrow">MemGuard / Enterprise handover</p><h1>Preparing the governed handover</h1><span className="mg-loading-line" aria-label="Loading" /></main>

  return (
    <div className="mg-app">
      <header className="mg-topbar">
        <div className="mg-brand"><span className="mg-wordmark">MEMGUARD</span><span className="mg-product-label">ENTERPRISE HANDOVER</span></div>
        <div className="mg-topbar__actions">
          <a className="mg-button" href="/">Evidence console</a>
          <a className="mg-button" href="/agent">Support agent</a>
          <button type="button" className="mg-button mg-button--primary" onClick={() => { void logout() }}>Sign out</button>
        </div>
      </header>
      <EnterpriseHandoverDemo report={report} />
    </div>
  )
}
