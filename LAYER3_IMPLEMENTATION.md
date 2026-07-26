# Layer 3 Implementation Guide

**Goal:** Build Claude.ai-style dashboard with 3 views - Memory Timeline, Decision Trace, Summary Card

**Priority:** 🎯 MEDIUM - Polish the demo experience

---

## Design Principles

**Inspired by Claude.ai:**
- Minimalist and clean
- Lots of white space
- Soft shadows and rounded corners
- Purple accent color (#7C3AED)
- Fast and responsive
- Clear visual hierarchy

**Three Views Only:**
1. Memory Timeline - Chronological event list
2. Decision Trace - Interactive causal chain
3. Summary Card - Business-friendly overview

**All in English, no Chinese text**

---

## Color Palette

### Claude.ai Inspired Colors

```css
Primary Purple:    #7C3AED (purple-600)
Light Purple:      #8B5CF6 (purple-500)
Background:        #FFFFFF (white)
Card Background:   #F9FAFB (gray-50)
Border:            #E5E7EB (gray-200)
Text Primary:      #111827 (gray-900)
Text Secondary:    #6B7280 (gray-500)
Text Dim:          #9CA3AF (gray-400)

Accent Colors:
Success:           #10B981 (green-500)
Warning:           #F59E0B (amber-500)
Error:             #EF4444 (red-500)
Info:              #3B82F6 (blue-500)
```

### Memory Type Colors

```css
Episodic:          #3B82F6 (blue-500)
Semantic:          #A855F7 (purple-500)
Procedural:        #06B6D4 (cyan-500)
Working:           #6B7280 (gray-500)
User Prefs:        #F59E0B (amber-500)
```

### Operation Colors

```css
CREATE:            #10B981 (green-500)
READ:              #3B82F6 (blue-500)
UPDATE:            #F59E0B (amber-500)
DELETE:            #EF4444 (red-500)
QUERY:             #8B5CF6 (purple-500)
```

---

## Architecture

```
dashboard/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Global styles
├── components/
│   ├── MemoryTimeline.tsx  # View 1
│   ├── DecisionTrace.tsx   # View 2
│   ├── SummaryCard.tsx     # View 3
│   ├── Header.tsx          # Dashboard header
│   └── StatsBar.tsx        # Quick stats
├── lib/
│   ├── api.ts              # API client
│   └── types.ts            # TypeScript types
├── public/
└── package.json
```

---

## Task Breakdown

### Task 1: Setup Next.js Project (30 min)

**Create new Next.js app:**

```bash
cd /Users/chakeswu/cursor/MemguardV1
npx create-next-app@latest dashboard --typescript --tailwind --app --no-src-dir
cd dashboard
```

**Install dependencies:**

```bash
npm install axios swr
```

**Configure `tailwind.config.js`:**

```javascript
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#7C3AED',
        'primary-light': '#8B5CF6',
      },
    },
  },
  plugins: [],
}
```

---

### Task 2: Create API Client (30 min)

**File:** `lib/api.ts`

```typescript
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface MemoryEvent {
  event_id: string
  agent_id: string
  session_id: string
  operation: string
  memory_key: string
  memory_type: string
  content_hash: string
  timestamp: string
  context?: Record<string, any>
  before_value?: any
  after_value?: any
}

export interface DecisionTrace {
  trace_id: string
  agent_id: string
  session_id: string
  timestamp: string
  input_memory_influences: MemoryInfluence[]
  total_input_influence: number
  decision_type: string
  decision_confidence: number
  decision_reasoning: string
  key_factors: string[]
  output_memory_influences: MemoryOutput[]
  llm_output: string
}

export interface MemoryInfluence {
  event_id: string
  memory_key: string
  memory_type: string
  operation: string
  influence_score: number
  content_preview?: string
  similarity_score?: number
  timestamp: string
}

export interface MemoryOutput {
  event_id: string
  memory_key: string
  memory_type: string
  operation: string
  content_hash: string
  timestamp: string
}

export interface Stats {
  total_events: number
  total_decision_traces: number
  db_path: string
}

export const api = {
  // Get events
  async getEvents(params?: {
    limit?: number
    offset?: number
    operation?: string
    agent_id?: string
    session_id?: string
  }): Promise<{ events: MemoryEvent[]; total: number }> {
    const response = await axios.get(`${API_BASE_URL}/v1/events`, { params })
    return response.data
  },

  // Get stats
  async getStats(): Promise<Stats> {
    const response = await axios.get(`${API_BASE_URL}/v1/db/stats`)
    return response.data
  },

  // Get decision trace detail
  async getDecisionTrace(traceId: string): Promise<DecisionTrace> {
    const response = await axios.get(`${API_BASE_URL}/v1/decision-traces/${traceId}`)
    return response.data
  },

  // Health check
  async health(): Promise<{ status: string }> {
    const response = await axios.get(`${API_BASE_URL}/health`)
    return response.data
  },
}
```

**File:** `lib/types.ts`

```typescript
export type {
  MemoryEvent,
  DecisionTrace,
  MemoryInfluence,
  MemoryOutput,
  Stats,
} from './api'

export type MemoryType = 'episodic' | 'semantic' | 'procedural' | 'working' | 'user_preferences'
export type Operation = 'create' | 'read' | 'update' | 'delete' | 'query' | 'search'

export const MEMORY_TYPE_COLORS: Record<MemoryType, string> = {
  episodic: 'text-blue-600 bg-blue-50 border-blue-200',
  semantic: 'text-purple-600 bg-purple-50 border-purple-200',
  procedural: 'text-cyan-600 bg-cyan-50 border-cyan-200',
  working: 'text-gray-600 bg-gray-50 border-gray-200',
  user_preferences: 'text-amber-600 bg-amber-50 border-amber-200',
}

export const OPERATION_COLORS: Record<Operation, string> = {
  create: 'text-green-600 bg-green-50 border-green-200',
  read: 'text-blue-600 bg-blue-50 border-blue-200',
  update: 'text-amber-600 bg-amber-50 border-amber-200',
  delete: 'text-red-600 bg-red-50 border-red-200',
  query: 'text-purple-600 bg-purple-50 border-purple-200',
  search: 'text-purple-600 bg-purple-50 border-purple-200',
}

export const OPERATION_ICONS: Record<Operation, string> = {
  create: '🟢',
  read: '🔵',
  update: '🟡',
  delete: '🔴',
  query: '🔷',
  search: '🔷',
}
```

---

### Task 3: Create Memory Timeline Component (2 hours)

**File:** `components/MemoryTimeline.tsx`

**Features:**
- Chronological list of memory events
- Filters by operation, agent, memory type
- Color-coded badges
- Real-time updates (polling every 2s during demo)
- Clean Claude.ai aesthetic

**Key UI Elements:**
```tsx
// Event card
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
  <div className="flex items-center justify-between">
    <span className="text-sm font-mono text-gray-500">
      {event.timestamp}
    </span>
    <span className={operationClass}>
      {icon} {operation.toUpperCase()}
    </span>
  </div>
  <div className="mt-2">
    <span className={memoryTypeClass}>
      {memory_type}:{memory_key}
    </span>
  </div>
  <div className="text-sm text-gray-500 mt-1">
    Agent: {agent_id}
  </div>
</div>
```

---

### Task 4: Create Decision Trace Component (2 hours)

**File:** `components/DecisionTrace.tsx`

**Features:**
- Visual causal chain: Memory IN → Decision → Memory OUT
- Influence score bars
- Expandable sections
- Content previews
- Interactive hover states

**Key UI Elements:**
```tsx
// Memory IN section
<div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-6">
  <h3 className="text-lg font-semibold text-gray-900 mb-4">
    Memory IN
  </h3>
  {influences.map(inf => (
    <div className="bg-white rounded-lg p-4 mb-3 shadow-sm">
      <div className="font-medium">{inf.memory_key}</div>
      <div className="text-sm text-gray-500 mt-1">
        {inf.content_preview}
      </div>
      {/* Influence bar */}
      <div className="mt-2 flex items-center">
        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-green-500"
            style={{ width: `${inf.influence_score * 100}%` }}
          />
        </div>
        <span className="ml-2 text-sm font-medium">
          {inf.influence_score.toFixed(2)}
        </span>
      </div>
    </div>
  ))}
</div>

// Arrow
<div className="flex justify-center my-4">
  <div className="text-4xl text-purple-500">↓</div>
</div>

// Decision section
<div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-6">
  <h3 className="text-lg font-semibold text-gray-900 mb-4">
    Agent Decision
  </h3>
  <div className="bg-white rounded-lg p-4 shadow-sm">
    <div className="text-xl font-bold text-red-600 mb-2">
      {decision_type.toUpperCase().replace('_', ' ')}
    </div>
    <div className="text-sm text-gray-600 mb-3">
      Confidence: {(decision_confidence * 100).toFixed(0)}%
    </div>
    <div className="text-sm text-gray-700">
      {decision_reasoning}
    </div>
  </div>
</div>

// Arrow
<div className="flex justify-center my-4">
  <div className="text-4xl text-purple-500">↓</div>
</div>

// Memory OUT section
<div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6">
  <h3 className="text-lg font-semibold text-gray-900 mb-4">
    Memory OUT
  </h3>
  {outputs.map(out => (
    <div className="bg-white rounded-lg p-4 mb-3 shadow-sm">
      <div className="font-medium">{out.memory_key}</div>
      <div className="text-sm text-gray-500 mt-1 font-mono">
        Hash: {out.content_hash.slice(0, 16)}...
      </div>
    </div>
  ))}
</div>
```

---

### Task 5: Create Summary Card Component (1 hour)

**File:** `components/SummaryCard.tsx`

**Features:**
- Business-friendly case overview
- Key findings as bullet points
- System performance metrics
- Download report button (future)

**Key UI Elements:**
```tsx
<div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 max-w-4xl mx-auto">
  {/* Header */}
  <div className="border-b border-gray-200 pb-6 mb-6">
    <h2 className="text-2xl font-bold text-gray-900">
      Compliance Case Summary
    </h2>
    <p className="text-gray-500 mt-1">
      Scenario 02: Structuring Detection
    </p>
  </div>

  {/* Case Details */}
  <div className="grid grid-cols-2 gap-6 mb-8">
    <div>
      <div className="text-sm text-gray-500">Case ID</div>
      <div className="text-lg font-semibold">TXN-2024-071001</div>
    </div>
    <div>
      <div className="text-sm text-gray-500">Amount</div>
      <div className="text-lg font-semibold">HKD 1,470,000</div>
    </div>
    <div>
      <div className="text-sm text-gray-500">Risk Assessment</div>
      <div className="text-lg font-bold text-red-600">CRITICAL (0.93)</div>
    </div>
    <div>
      <div className="text-sm text-gray-500">Decision</div>
      <div className="text-lg font-bold text-red-600">FILE SAR</div>
    </div>
  </div>

  {/* Key Findings */}
  <div className="mb-8">
    <h3 className="text-lg font-semibold mb-3">Key Findings</h3>
    <ul className="space-y-2">
      <li className="flex items-start">
        <span className="text-red-500 mr-2">•</span>
        <span className="text-gray-700">
          Customer split large amount to avoid threshold
        </span>
      </li>
      {/* More findings... */}
    </ul>
  </div>

  {/* AI Performance */}
  <div className="bg-gray-50 rounded-lg p-6">
    <h3 className="text-lg font-semibold mb-4">AI System Performance</h3>
    <div className="grid grid-cols-3 gap-4">
      <div>
        <div className="text-2xl font-bold text-primary">11</div>
        <div className="text-sm text-gray-500">Memory Operations</div>
      </div>
      <div>
        <div className="text-2xl font-bold text-primary">4</div>
        <div className="text-sm text-gray-500">Agents</div>
      </div>
      <div>
        <div className="text-2xl font-bold text-primary">6.7s</div>
        <div className="text-sm text-gray-500">Analysis Time</div>
      </div>
    </div>
  </div>
</div>
```

---

### Task 6: Create Main Dashboard Page (1 hour)

**File:** `app/page.tsx`

**Features:**
- Three-tab layout
- Real-time stats bar at top
- Polling for updates during demo
- Loading states
- Error handling

**Structure:**
```tsx
'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'
import MemoryTimeline from '@/components/MemoryTimeline'
import DecisionTrace from '@/components/DecisionTrace'
import SummaryCard from '@/components/SummaryCard'
import { api } from '@/lib/api'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'timeline' | 'trace' | 'summary'>('timeline')
  
  // Poll stats every 2s
  const { data: stats, error } = useSWR('stats', () => api.getStats(), {
    refreshInterval: 2000
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            MemGuard Dashboard
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Memory Observability for AI Agents
          </p>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex gap-8">
            <div>
              <span className="text-gray-500 text-sm">Total Events</span>
              <span className="ml-2 font-semibold">{stats?.total_events || 0}</span>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Decision Traces</span>
              <span className="ml-2 font-semibold">{stats?.total_decision_traces || 0}</span>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Status</span>
              <span className="ml-2 text-green-600 font-semibold">● Live</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex gap-8">
            {['timeline', 'trace', 'summary'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'timeline' && <MemoryTimeline />}
        {activeTab === 'trace' && <DecisionTrace />}
        {activeTab === 'summary' && <SummaryCard />}
      </main>
    </div>
  )
}
```

---

### Task 7: Polish & Test (1 hour)

**Checklist:**

- [ ] All colors match Claude.ai aesthetic
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Loading states for all data fetching
- [ ] Error states with retry buttons
- [ ] Smooth transitions and animations
- [ ] Accessibility (keyboard navigation, ARIA labels)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Real-time updates working
- [ ] All English text (no Chinese)
- [ ] Performance optimized (no lag)

**Testing Commands:**

```bash
# Development
npm run dev

# Production build
npm run build
npm start

# Type check
npm run type-check
```

---

## Success Criteria

### Visual Quality
- [ ] Looks like Claude.ai (minimalist, clean, professional)
- [ ] Color palette consistent throughout
- [ ] Proper spacing and typography
- [ ] Smooth animations

### Functionality
- [ ] All 3 views working
- [ ] Real-time updates during demo
- [ ] Filters work correctly
- [ ] No errors in console

### Performance
- [ ] Page loads in <2s
- [ ] No lag during updates
- [ ] Smooth scrolling
- [ ] Efficient re-renders

### User Experience
- [ ] Clear navigation
- [ ] Intuitive interactions
- [ ] Helpful error messages
- [ ] Mobile-friendly

---

## Execution Prompt for Layer 3

**Prompt to give to Claude Code:**

```
I need you to implement Layer 3 of the MemGuard demo: Claude-style Dashboard.

Read the architecture: DEMO_ARCHITECTURE.md
Read this guide: LAYER3_IMPLEMENTATION.md

Your tasks:
1. Setup Next.js 14 project with TypeScript and Tailwind CSS
2. Create API client (lib/api.ts) with TypeScript types
3. Implement MemoryTimeline component (chronological event list)
4. Implement DecisionTrace component (causal chain visualization)
5. Implement SummaryCard component (business-friendly summary)
6. Create main dashboard page with 3-tab layout
7. Add real-time updates with polling
8. Polish with Claude.ai aesthetic

Requirements:
- Claude.ai design style (minimal, clean, purple accents)
- All English text (no Chinese)
- Real-time updates (poll every 2s during demo)
- Responsive design
- Type-safe with TypeScript
- Fast and smooth

After implementation:
- Test with: npm run dev
- Verify all 3 views work
- Check real-time updates
- Show me screenshots
```

---

**End of Layer 3 Implementation Guide**
