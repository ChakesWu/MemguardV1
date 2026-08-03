import { describe, expect, it } from 'vitest'

import { agentClientOptions } from '../lib/agent-client'

describe('agent client configuration', () => {
  it('sends the Keycloak access token only to the authenticated backend proxy', () => {
    expect(agentClientOptions('access-token-123')).toEqual({
      apiUrl: '/api/v1/agent-server',
      defaultHeaders: { Authorization: 'Bearer access-token-123' },
    })
  })

  it('rejects an empty browser token', () => {
    expect(() => agentClientOptions('')).toThrow('access token')
  })
})
