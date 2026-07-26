'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { api } from '@/lib/api'

const OP_COLORS: Record<string, string> = {
  create: 'bg-green-50 text-green-700 border-green-200',
  read: 'bg-blue-50 text-blue-700 border-blue-200',
  update: 'bg-amber-50 text-amber-700 border-amber-200',
  delete: 'bg-red-50 text-red-700 border-red-200',
  query: 'bg-purple-50 text-purple-700 border-purple-200',
}

const MEMORY_COLORS: Record<string, string> = {
  episodic: 'bg-blue-50 text-blue-600',
  semantic: 'bg-purple-50 text-purple-600',
  procedural: 'bg-cyan-50 text-cyan-600',
  working: 'bg-gray-50 text-gray-600',
}

const OP_ICONS: Record<string, string> = {
  create: '🟢',
  read: '🔵',
  update: '🟡',
  delete: '🔴',
  query: '🔷',
}

export default function MemoryTimeline() {
  const [filter, setFilter] = useState<string>('all')

  const { data, error } = useSWR('events', () => api.getEvents({ limit: 50 }), {
    refreshInterval: 2000,
    onError: () => {}
  })

  const events = data?.events || []
  const filtered = filter === 'all' ? events : events.filter(e => e.operation === filter)

  return (
    <div>
      {/* Filters */}
      <div className="mb-6 flex gap-3">
        {['all', 'create', 'read', 'update', 'query'].map(op => (
          <button
            key={op}
            onClick={() => setFilter(op)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === op
                ? 'bg-purple-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {op === 'all' ? 'All' : op.charAt(0).toUpperCase() + op.slice(1)}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <p className="text-gray-500">No events yet. Run demo.py to generate events.</p>
          </div>
        ) : (
          filtered.map((event) => (
            <div
              key={event.event_id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Operation & Time */}
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-3 py-1 rounded-md text-xs font-medium border ${OP_COLORS[event.operation] || 'bg-gray-50 text-gray-600'}`}>
                      {OP_ICONS[event.operation]} {event.operation.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  {/* Memory Key */}
                  <div className="mb-2">
                    <span className={`px-2 py-1 rounded text-sm font-medium ${MEMORY_COLORS[event.memory_type] || 'bg-gray-50 text-gray-600'}`}>
                      {event.memory_type}
                    </span>
                    <span className="ml-2 text-sm font-mono text-gray-700">
                      {event.memory_key}
                    </span>
                  </div>

                  {/* Agent */}
                  <div className="text-xs text-gray-500">
                    Agent: <span className="font-medium text-gray-700">{event.agent_id}</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Stats */}
      {filtered.length > 0 && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Showing {filtered.length} of {events.length} events
        </div>
      )}
    </div>
  )
}
