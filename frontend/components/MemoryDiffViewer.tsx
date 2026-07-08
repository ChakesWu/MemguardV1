'use client'

import { useMemo, useState } from 'react'

// ── Types ────────────────────────────────────────────────────────

interface DiffLine {
  type: 'unchanged' | 'added' | 'removed' | 'modified'
  key: string
  beforeLine: string
  afterLine: string
  indent: number
}

// ── Diff Engine ───────────────────────────────────────────────────

function parseObj(obj: any, prefix: string = ''): Record<string, string> {
  const flat: Record<string, string> = {}
  if (typeof obj === 'string') {
    flat[prefix || 'value'] = JSON.stringify(obj)
  } else if (obj === null || obj === undefined) {
    flat[prefix || 'value'] = String(obj)
  } else if (Array.isArray(obj)) {
    obj.forEach((item, i) => {
      const k = prefix ? `${prefix}[${i}]` : `[${i}]`
      if (typeof item === 'object' && item !== null) {
        Object.assign(flat, parseObj(item, k))
      } else {
        flat[k] = JSON.stringify(item)
      }
    })
  } else if (typeof obj === 'object') {
    const entries = Object.entries(obj)
    if (entries.length === 0) {
      flat[prefix || '(empty)'] = '{}'
    }
    entries.forEach(([k, v]) => {
      const key = prefix ? `${prefix}.${k}` : k
      if (typeof v === 'object' && v !== null) {
        Object.assign(flat, parseObj(v, key))
      } else {
        flat[key] = JSON.stringify(v)
      }
    })
  } else {
    flat[prefix || 'value'] = JSON.stringify(obj)
  }
  return flat
}

function buildDiff(before: any, after: any): DiffLine[] {
  const beforeFlat = parseObj(before)
  const afterFlat = parseObj(after)

  const allKeys = new Set([...Object.keys(beforeFlat), ...Object.keys(afterFlat)])
  const sorted = [...allKeys].sort()

  const lines: DiffLine[] = sorted.map(key => {
    const beforeVal = beforeFlat[key]
    const afterVal = afterFlat[key]
    const indent = (key.match(/\.|\[/g) || []).length

    if (!(key in beforeFlat) && key in afterFlat) {
      return { type: 'added', key, beforeLine: '', afterLine: `${key}: ${afterVal}`, indent }
    }
    if (key in beforeFlat && !(key in afterFlat)) {
      return { type: 'removed', key, beforeLine: `${key}: ${beforeVal}`, afterLine: '', indent }
    }
    if (beforeVal !== afterVal) {
      return {
        type: 'modified',
        key,
        beforeLine: `${key}: ${beforeVal}`,
        afterLine: `${key}: ${afterVal}`,
        indent,
      }
    }
    return { type: 'unchanged', key, beforeLine: `${key}: ${beforeVal}`, afterLine: `${key}: ${afterVal}`, indent }
  })

  return lines
}

// ── Change Pulse ──────────────────────────────────────────────────

export function ChangePulse({ count, size = 8 }: { count: number; size?: number }) {
  if (count === 0) return <span className="text-gray-600 text-xs">no changes</span>

  const intensity = Math.min(count / 10, 1.0)
  const ringSize = size + intensity * 8

  return (
    <span className="inline-flex items-center gap-1.5" title={`${count} field${count > 1 ? 's' : ''} changed`}>
      <span className="relative inline-flex" style={{ width: ringSize + 4, height: ringSize + 4 }}>
        <span
          className="absolute inset-0 rounded-full animate-ping opacity-30"
          style={{
            width: ringSize + 4,
            height: ringSize + 4,
            animationDuration: `${2 - intensity * 0.8}s`,
            backgroundColor: `rgba(255, 180, 60, ${0.3 + intensity * 0.4})`,
          }}
        />
        <span
          className="absolute rounded-full"
          style={{
            width: size,
            height: size,
            left: (ringSize + 4 - size) / 2,
            top: (ringSize + 4 - size) / 2,
            backgroundColor: intensity > 0.5 ? '#f59e0b' : '#d97706',
          }}
        />
      </span>
      <span className="text-[10px] font-medium tracking-wider uppercase text-amber-400/80">
        {count} change{count > 1 ? 's' : ''}
      </span>
    </span>
  )
}

// ── Main Diff Viewer ──────────────────────────────────────────────

export default function MemoryDiffViewer({ before, after }: { before: any; after: any }) {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'unified'>('side-by-side')
  const [collapsed, setCollapsed] = useState(false)

  const diffLines = useMemo(() => buildDiff(before, after), [before, after])
  const changedCount = diffLines.filter(d => d.type !== 'unchanged').length

  if (!before && !after) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No state data available for diff
      </div>
    )
  }

  // Edge case: no after = CREATE (show everything as added)
  const effectiveBefore = before || {}
  const effectiveAfter = after || {}

  return (
    <div className="font-mono text-sm border border-gray-800/80 rounded-lg overflow-hidden bg-[#0b0f17]">
      {/* ── Diff Header ──────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#111820] border-b border-gray-800/60">
        <div className="flex items-center gap-3">
          <ChangePulse count={changedCount} size={9} />

          <div className="flex items-center gap-1.5 text-[10px] tracking-wider uppercase text-gray-500">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2.5 py-1 rounded transition-colors ${
                viewMode === 'side-by-side'
                  ? 'bg-gray-700/80 text-gray-200'
                  : 'hover:text-gray-300'
              }`}
            >
              Split
            </button>
            <button
              onClick={() => setViewMode('unified')}
              className={`px-2.5 py-1 rounded transition-colors ${
                viewMode === 'unified'
                  ? 'bg-gray-700/80 text-gray-200'
                  : 'hover:text-gray-300'
              }`}
            >
              Unified
            </button>
          </div>

          <div className="flex items-center gap-1.5 ml-2 text-[11px]">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#591d2e' }} />
              <span className="text-gray-500">-{diffLines.filter(d => d.type === 'removed').length}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#0d3928' }} />
              <span className="text-gray-500">+{diffLines.filter(d => d.type === 'added').length}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#1a2a3d' }} />
              <span className="text-gray-500">~{diffLines.filter(d => d.type === 'modified').length}</span>
            </span>
          </div>
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-gray-500 hover:text-gray-300 text-xs transition-colors px-2 py-0.5"
        >
          {collapsed ? 'Expand' : 'Collapse'}
        </button>
      </div>

      {/* ── Diff Body ────────────────────────────────── */}
      {!collapsed && (
        <div className={`${viewMode === 'side-by-side' ? 'grid grid-cols-2 divide-x divide-gray-800/60' : ''}`}>
          {viewMode === 'side-by-side' ? (
            <>
              {/* Before column */}
              <div className="overflow-x-auto">
                {diffLines.map((line, i) => (
                  <div
                    key={`b-${i}`}
                    className="flex"
                    style={{
                      backgroundColor:
                        line.type === 'removed' ? 'rgba(89, 29, 46, 0.6)' :
                        line.type === 'modified' ? 'rgba(26, 42, 61, 0.5)' :
                        'transparent',
                      borderLeft: line.type === 'removed'
                        ? '3px solid #c62828'
                        : line.type === 'modified'
                        ? '3px solid #d97706'
                        : '3px solid transparent',
                    }}
                  >
                    <span className="flex-none w-8 text-right pr-3 text-gray-600 text-xs leading-6 pt-px select-none">
                      {i + 1}
                    </span>
                    <span
                      className={`flex-1 leading-6 py-px px-2 whitespace-pre text-xs ${
                        line.type === 'removed' ? 'text-[#ff8a80]' :
                        line.type === 'modified' ? 'text-[#ffb74d]' :
                        'text-gray-400'
                      }`}
                      style={{ paddingLeft: `${line.indent * 16 + 8}px` }}
                    >
                      {line.beforeLine || ' '}
                    </span>
                  </div>
                ))}
              </div>

              {/* After column */}
              <div className="overflow-x-auto">
                {diffLines.map((line, i) => (
                  <div
                    key={`a-${i}`}
                    className="flex"
                    style={{
                      backgroundColor:
                        line.type === 'added' ? 'rgba(13, 57, 40, 0.6)' :
                        line.type === 'modified' ? 'rgba(26, 42, 61, 0.35)' :
                        'transparent',
                      borderLeft: line.type === 'added'
                        ? '3px solid #2e7d32'
                        : line.type === 'modified'
                        ? '3px solid #d97706'
                        : '3px solid transparent',
                    }}
                  >
                    <span className="flex-none w-8 text-right pr-3 text-gray-600 text-xs leading-6 pt-px select-none">
                      {i + 1}
                    </span>
                    <span
                      className={`flex-1 leading-6 py-px px-2 whitespace-pre text-xs ${
                        line.type === 'added' ? 'text-[#69f0ae]' :
                        line.type === 'modified' ? 'text-[#ffb74d]' :
                        'text-gray-400'
                      }`}
                      style={{ paddingLeft: `${line.indent * 16 + 8}px` }}
                    >
                      {line.afterLine || ' '}
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            /* Unified view */
            <div className="overflow-x-auto">
              {diffLines.map((line, i) => (
                <div
                  key={`u-${i}`}
                  className="flex"
                  style={{
                    backgroundColor:
                      line.type === 'removed' ? 'rgba(89, 29, 46, 0.45)' :
                      line.type === 'added' ? 'rgba(13, 57, 40, 0.45)' :
                      line.type === 'modified' ? 'rgba(26, 42, 61, 0.3)' :
                      'transparent',
                  }}
                >
                  <span className="flex-none w-6 text-center text-gray-600 text-xs leading-6 select-none">
                    {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
                  </span>
                  <span className="flex-none w-8 text-right pr-3 text-gray-600 text-xs leading-6 select-none">
                    {i + 1}
                  </span>
                  <span
                    className={`flex-1 leading-6 py-px px-2 whitespace-pre text-xs ${
                      line.type === 'removed' ? 'text-[#ff8a80]' :
                      line.type === 'added' ? 'text-[#69f0ae]' :
                      line.type === 'modified' ? 'text-[#ffb74d]' :
                      'text-gray-400'
                    }`}
                    style={{ paddingLeft: `${line.indent * 16 + 8}px` }}
                  >
                    {line.type === 'removed' ? line.beforeLine : line.afterLine || ' '}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Collapsed summary ──────────────────────── */}
      {collapsed && changedCount > 0 && (
        <div className="px-4 py-3 text-sm text-gray-400">
          <span className="text-[#ff8a80]">-{diffLines.filter(d => d.type === 'removed').length} removed</span>
          {' · '}
          <span className="text-[#69f0ae]">+{diffLines.filter(d => d.type === 'added').length} added</span>
          {' · '}
          <span className="text-[#ffb74d]">~{diffLines.filter(d => d.type === 'modified').length} modified</span>
        </div>
      )}
    </div>
  )
}
