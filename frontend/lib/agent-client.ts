import { Client } from '@langchain/langgraph-sdk'

export const AGENT_SERVER_API_PATH = '/api/v1/agent-server'
export const CUSTOMER_SUPPORT_ASSISTANT_ID = 'customer_support_agent'
export const CUSTOMER_SUPPORT_STREAM_MODES: 'values'[] = ['values']

export function agentServerApiUrl(origin?: string) {
  return origin ? new URL(AGENT_SERVER_API_PATH, origin).toString() : AGENT_SERVER_API_PATH
}

export function agentClientOptions(accessToken: string) {
  if (!accessToken.trim()) {
    throw new Error('A Keycloak access token is required for the customer-support agent.')
  }
  return {
    apiUrl: agentServerApiUrl(typeof window === 'undefined' ? undefined : window.location.origin),
    defaultHeaders: { Authorization: `Bearer ${accessToken}` },
  }
}

export function createAgentClient(accessToken: string) {
  return new Client(agentClientOptions(accessToken))
}
