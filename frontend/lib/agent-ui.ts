export type ApprovalInterrupt = {
  action: string
  arguments: Record<string, unknown>
  policyDecision: string
  policyVersion: string
  allowedDecisions: string[]
}

export function parseApprovalInterrupt(value: unknown): ApprovalInterrupt | null {
  if (!value || typeof value !== 'object') return null
  const candidate = value as Record<string, unknown>
  if (candidate.kind !== 'approval_required' || typeof candidate.action !== 'string') return null
  return {
    action: candidate.action,
    arguments: typeof candidate.arguments === 'object' && candidate.arguments !== null
      ? candidate.arguments as Record<string, unknown>
      : {},
    policyDecision: typeof candidate.policy_decision === 'string' ? candidate.policy_decision : 'review required',
    policyVersion: typeof candidate.policy_version === 'string' ? candidate.policy_version : 'current policy',
    allowedDecisions: Array.isArray(candidate.allowed_decisions)
      ? candidate.allowed_decisions.filter((item): item is string => typeof item === 'string')
      : [],
  }
}

export function messageText(content: unknown): string {
  if (typeof content === 'string') return content
  if (!Array.isArray(content)) return ''
  return content
    .map((part) => {
      if (typeof part === 'string') return part
      if (part && typeof part === 'object' && 'text' in part && typeof part.text === 'string') return part.text
      return ''
    })
    .filter(Boolean)
    .join('\n')
}
