import { describe, expect, it } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

describe('real agent memory inventory', () => {
  it('renders memory content before technical identifiers and explains usage status', () => {
    const component = join(process.cwd(), 'components', 'MemoryInventory.tsx')
    expect(existsSync(component)).toBe(true)
    const source = readFileSync(component, 'utf8')
    expect(source).toContain('What the agent actually remembers')
    expect(source).toContain('Used in this answer')
    expect(source).toContain('Rejected by policy')
    expect(source).toContain('Why this memory was used')
    expect(source).toContain('Technical details')
  })
})
