import { describe, expect, it } from 'vitest'

import { CUSTOMER_SUPPORT_STREAM_MODES, agentClientOptions, agentServerApiUrl } from '../lib/agent-client'

describe('agent client configuration', () => {
  it('sends the Keycloak access token only to the authenticated backend proxy', () => {
    expect(agentClientOptions('access-token-123')).toEqual({
      apiUrl: '/api/v1/agent-server',
      defaultHeaders: { Authorization: 'Bearer access-token-123' },
    })
  })

  it('builds an absolute URL when running in the browser', () => {
    expect(agentServerApiUrl('http://localhost:3001')).toBe('http://localhost:3001/api/v1/agent-server')
  })

  it('uses only LangGraph Server-supported stream modes', () => {
    expect(CUSTOMER_SUPPORT_STREAM_MODES).toEqual(['values'])
  })

  it('rejects an empty browser token', () => {
    expect(() => agentClientOptions('')).toThrow('access token')
  })
})
