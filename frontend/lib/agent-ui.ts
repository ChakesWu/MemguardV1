export type ApprovalInterrupt = {
  action: string
  arguments: Record<string, unknown>
  policyDecision: string
  policyVersion: string
  allowedDecisions: string[]
}

export type OutputEvidenceLink = {
  startOffset: number
  endOffset: number
  segment: string
  memoryId: string
  evidenceQuote: string
  role: string
  trustScore: number | null
  trustLevel: string
  policyAction: string
  sourceType: string | null
  sourceId: string | null
}

export type OutputEvidencePart =
  | { kind: 'text'; text: string }
  | { kind: 'evidence'; text: string; links: OutputEvidenceLink[] }

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

export function shouldRenderChatMessage(message: unknown): boolean {
  const type = record(message)?.type
  return type === 'human' || type === 'ai' || type === 'assistant'
}

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null
}

function validOffset(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0
}

/**
 * Converts an SDK evidence report into display data, failing closed if a link
 * is not explicit, prompt-included, or cannot be mapped to the visible answer.
 */
export function parseOutputEvidence(answer: string, report: unknown): OutputEvidenceLink[] {
  const payload = record(report)
  const outputEvidence = record(payload?.output_evidence)
  const links = outputEvidence?.valid_links
  const items = Array.isArray(payload?.items) ? payload.items : []
  if (!Array.isArray(links)) return []

  const sources = new Map(
    items.flatMap((item) => {
      const memory = record(item)
      const memoryId = memory?.memory_id
      const source = record(memory?.source)
      return typeof memoryId === 'string'
        ? [[memoryId, {
          type: typeof source?.type === 'string' ? source.type : null,
          id: typeof source?.id === 'string' ? source.id : null,
        }] as const]
        : []
    }),
  )

  return links.flatMap((value) => {
    const link = record(value)
    const trust = record(link?.trust)
    const policy = record(link?.policy)
    const start = link?.start_offset
    const end = link?.end_offset
    const segment = link?.segment
    const memoryId = link?.memory_id
    const quote = link?.evidence_quote
    const role = link?.role
    const included = link?.prompt_included
    const validation = link?.validation_status
    const trustScore = trust?.score
    const policyAction = policy?.action
    if (
      !validOffset(start) || !validOffset(end) || start >= end || end > answer.length ||
      typeof segment !== 'string' || answer.slice(start, end) !== segment ||
      typeof memoryId !== 'string' || !memoryId || typeof quote !== 'string' ||
      typeof role !== 'string' || included !== true || validation !== 'valid' ||
      (typeof trustScore !== 'number' && trustScore !== null) ||
      typeof policyAction !== 'string'
    ) return []

    const source = sources.get(memoryId)
    return [{
      startOffset: start,
      endOffset: end,
      segment,
      memoryId,
      evidenceQuote: quote,
      role,
      trustScore,
      trustLevel: typeof trust?.level === 'string' ? trust.level : 'unknown',
      policyAction,
      sourceType: source?.type ?? null,
      sourceId: source?.id ?? null,
    }]
  })
}

export function parseMessageOutputEvidence(answer: string, message: unknown): OutputEvidenceLink[] {
  const metadata = record(record(message)?.additional_kwargs)
  return parseOutputEvidence(answer, metadata?.memguard_output_evidence)
}

export function outputEvidenceParts(answer: string, links: OutputEvidenceLink[]): OutputEvidencePart[] {
  const groups = new Map<string, OutputEvidenceLink[]>()
  for (const link of links) {
    const key = `${link.startOffset}:${link.endOffset}`
    groups.set(key, [...(groups.get(key) || []), link])
  }

  const ranges = [...groups.values()]
    .map((rangeLinks) => ({
      start: rangeLinks[0].startOffset,
      end: rangeLinks[0].endOffset,
      links: rangeLinks,
    }))
    .sort((left, right) => left.start - right.start || left.end - right.end)

  const parts: OutputEvidencePart[] = []
  let cursor = 0
  for (const range of ranges) {
    if (range.start < cursor) continue
    if (range.start > cursor) parts.push({ kind: 'text', text: answer.slice(cursor, range.start) })
    parts.push({ kind: 'evidence', text: answer.slice(range.start, range.end), links: range.links })
    cursor = range.end
  }
  if (cursor < answer.length) parts.push({ kind: 'text', text: answer.slice(cursor) })
  return parts.length ? parts : [{ kind: 'text', text: answer }]
}
