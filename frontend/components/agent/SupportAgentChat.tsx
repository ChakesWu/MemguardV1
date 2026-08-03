'use client'

import { FormEvent, useMemo, useState } from 'react'
import { useStream } from '@langchain/langgraph-sdk/react'

import { CUSTOMER_SUPPORT_ASSISTANT_ID, CUSTOMER_SUPPORT_STREAM_MODES, agentClientOptions } from '../../lib/agent-client'
import { messageText, parseApprovalInterrupt } from '../../lib/agent-ui'

type SupportAgentChatProps = {
  accessToken: string
  onSignOut: () => void
}

export default function SupportAgentChat({ accessToken, onSignOut }: SupportAgentChatProps) {
  const [draft, setDraft] = useState('')
  const [threadId, setThreadId] = useState<string | null>(null)
  const stream = useStream({
    ...agentClientOptions(accessToken),
    assistantId: CUSTOMER_SUPPORT_ASSISTANT_ID,
    threadId,
    onThreadId: setThreadId,
    fetchStateHistory: true,
  })
  const approval = useMemo(() => parseApprovalInterrupt(stream.interrupt?.value), [stream.interrupt])

  async function submitMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || stream.isLoading) return
    setDraft('')
    await stream.submit(
      { messages: [{ type: 'human', content: text }] },
      { streamMode: CUSTOMER_SUPPORT_STREAM_MODES, streamResumable: true },
    )
  }

  async function resolveApproval(decision: 'approve' | 'edit' | 'reject') {
    if (stream.isLoading) return
    await stream.submit(null, {
      command: { resume: { decision } },
      streamMode: CUSTOMER_SUPPORT_STREAM_MODES,
      streamResumable: true,
    })
  }

  return (
    <main className="mg-agent-page">
      <header className="mg-topbar mg-agent-topbar">
        <div className="mg-brand">
          <span className="mg-wordmark">MEMGUARD</span>
          <span className="mg-product-label">SUPPORT AGENT</span>
        </div>
        <div className="mg-topbar__actions">
          <a className="mg-button" href="/">Evidence console</a>
          <button type="button" className="mg-button" onClick={() => { stream.switchThread(null); setThreadId(null) }}>New conversation</button>
          <button type="button" className="mg-button mg-button--primary" onClick={onSignOut}>Sign out</button>
        </div>
      </header>

      <section className="mg-agent-shell" aria-label="Customer support agent">
        <aside className="mg-agent-context">
          <p className="mg-eyebrow">Real LangGraph workflow</p>
          <h1>Customer support with accountable actions.</h1>
          <p>The agent reads current order facts and policy. Any business action pauses for a human decision before it is recorded.</p>
          <dl>
            <div><dt>Order</dt><dd><code>ORD-4821</code></dd></div>
            <div><dt>Customer</dt><dd>Alex Chen · VIP</dd></div>
            <div><dt>Policy</dt><dd>Refund policy v2</dd></div>
          </dl>
          <button type="button" className="mg-agent-starter" onClick={() => setDraft('I need a refund for ORD-4821 because the item is defective.')}>Try the policy scenario</button>
          {threadId && <p className="mg-agent-thread">Thread <code>{threadId.slice(0, 8)}…</code></p>}
        </aside>

        <section className="mg-agent-chat">
          <header className="mg-agent-chat__header">
            <div>
              <p className="mg-eyebrow">Live conversation</p>
              <h2>Support desk</h2>
            </div>
            <span className={`mg-connection${stream.error ? '' : ' is-connected'}`}>{stream.error ? 'Connection error' : 'Agent ready'}</span>
          </header>

          <div className="mg-agent-messages" aria-live="polite">
            {stream.messages.length === 0 && (
              <div className="mg-agent-empty">
                <span>✦</span>
                <p>Ask about <code>ORD-4821</code>, or request a refund to see the human approval workflow.</p>
              </div>
            )}
            {stream.messages.map((message, index) => {
              const content = messageText(message.content)
              if (!content) return null
              const isUser = message.type === 'human'
              return (
                <article key={message.id || index} className={`mg-agent-message ${isUser ? 'mg-agent-message--user' : 'mg-agent-message--assistant'}`}>
                  <span className="mg-agent-message__label">{isUser ? 'You' : 'Support agent'}</span>
                  <p>{content}</p>
                </article>
              )
            })}
            {stream.isLoading && <div className="mg-agent-thinking"><span className="mg-loading-line" /> The agent is checking the available evidence…</div>}
            {Boolean(stream.error) && <p className="mg-agent-error">{stream.error instanceof Error ? stream.error.message : 'The agent request could not be completed.'}</p>}
          </div>

          {approval && (
            <section className="mg-agent-approval" aria-label="Human approval required">
              <p className="mg-eyebrow">Human approval required</p>
              <h3>{approval.action.replaceAll('_', ' ')}</h3>
              <p>This action is <strong>{approval.policyDecision.replaceAll('_', ' ')}</strong> under {approval.policyVersion}. No business record has been written yet.</p>
              <div className="mg-agent-approval__details">
                {Object.entries(approval.arguments).map(([key, value]) => <span key={key}><b>{key.replaceAll('_', ' ')}</b> {String(value)}</span>)}
              </div>
              <div className="mg-agent-approval__actions">
                {approval.allowedDecisions.includes('approve') && <button type="button" className="mg-button mg-button--primary" onClick={() => resolveApproval('approve')}>Approve</button>}
                {approval.allowedDecisions.includes('edit') && <button type="button" className="mg-button" onClick={() => resolveApproval('edit')}>Edit request</button>}
                {approval.allowedDecisions.includes('reject') && <button type="button" className="mg-button mg-button--warning" onClick={() => resolveApproval('reject')}>Reject</button>}
              </div>
            </section>
          )}

          <form className="mg-agent-composer" onSubmit={submitMessage}>
            <textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask about an order or make a support request…" rows={3} disabled={stream.isLoading} />
            <button type="submit" className="mg-button mg-button--primary" disabled={!draft.trim() || stream.isLoading}>Send</button>
          </form>
        </section>
      </section>
    </main>
  )
}
