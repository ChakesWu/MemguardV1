'use client'

import { useEffect, useState } from 'react'

import SupportAgentChat from '../../components/agent/SupportAgentChat'
import { loginRequired, logout } from '../../lib/auth'

export default function AgentPage() {
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loginRequired().then(setAccessToken).catch(() => setError('Unable to sign in with Keycloak. Check that the local identity service is running.'))
  }, [])

  if (error) {
    return <main className="mg-state-screen"><p className="mg-eyebrow">MemGuard / Support agent</p><h1>Sign-in unavailable</h1><p>{error}</p></main>
  }
  if (!accessToken) {
    return <main className="mg-state-screen"><p className="mg-eyebrow">MemGuard / Support agent</p><h1>Opening your support desk</h1><span className="mg-loading-line" aria-label="Loading" /></main>
  }
  return <SupportAgentChat accessToken={accessToken} onSignOut={() => { void logout() }} />
}
