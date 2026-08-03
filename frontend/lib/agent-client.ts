import { Client } from '@langchain/langgraph-sdk'

export const AGENT_SERVER_API_URL = '/api/v1/agent-server'
export const CUSTOMER_SUPPORT_ASSISTANT_ID = 'customer_support_agent'

export function agentClientOptions(accessToken: string) {
  if (!accessToken.trim()) {
    throw new Error('A Keycloak access token is required for the customer-support agent.')
  }
  return {
    apiUrl: AGENT_SERVER_API_URL,
    defaultHeaders: { Authorization: `Bearer ${accessToken}` },
  }
}

export function createAgentClient(accessToken: string) {
  return new Client(agentClientOptions(accessToken))
}
