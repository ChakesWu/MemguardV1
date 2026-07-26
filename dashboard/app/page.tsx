'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { api } from '@/lib/api'
import MemoryTimeline from '@/components/MemoryTimeline'
import DecisionTrace from '@/components/DecisionTrace'
import SummaryCard from '@/components/SummaryCard'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'timeline' | 'trace' | 'summary'>('summary')

  const { data: stats } = useSWR('stats', () => api.getStats(), {
    refreshInterval: 2000,
    onError: () => {}
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <h1 className="text-3xl font-bold text-gray-900">MemGuard</h1>
          <p className="text-gray-500 text-sm mt-1">Memory Observability for AI Agents</p>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex gap-8 text-sm">
            <div>
              <span className="text-gray-500">Total Events</span>
              <span className="ml-2 font-semibold text-gray-900">{stats?.total_events || 0}</span>
            </div>
            <div>
              <span className="text-gray-500">Decision Traces</span>
              <span className="ml-2 font-semibold text-gray-900">{stats?.total_decision_traces || 0}</span>
            </div>
            <div>
              <span className="text-gray-500">Status</span>
              <span className="ml-2 text-green-600 font-semibold">● Live</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex gap-8">
            {[
              { key: 'summary', label: 'Summary' },
              { key: 'timeline', label: 'Memory Timeline' },
              { key: 'trace', label: 'Decision Trace' }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.key
                    ? 'border-purple-600 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'summary' && <SummaryCard />}
        {activeTab === 'timeline' && <MemoryTimeline />}
        {activeTab === 'trace' && <DecisionTrace />}
      </main>
    </div>
  )
}
