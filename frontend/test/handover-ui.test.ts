import { describe, expect, it } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

describe('enterprise handover demo', () => {
  it('shows the three memory boundaries and an inspectable lineage panel', () => {
    const page = join(process.cwd(), 'app', 'handover', 'page.tsx')
    const component = join(process.cwd(), 'components', 'EnterpriseHandoverDemo.tsx')

    expect(existsSync(page)).toBe(true)
    expect(existsSync(component)).toBe(true)
    const source = readFileSync(component, 'utf8')
    expect(source).toContain('Company source of truth')
    expect(source).toContain('Departing employee agent')
    expect(source).toContain('Successor team agent')
    expect(source).toContain('Memory lineage')
    expect(source).toContain('protected')
    expect(source).toContain('redacted_for_review')
  })
})
