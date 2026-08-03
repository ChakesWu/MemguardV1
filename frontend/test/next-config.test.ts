import { describe, expect, it } from 'vitest'

import nextConfig from '../next.config'

describe('Next proxy rewrite', () => {
  it('uses the Docker backend hostname when configured at build time', async () => {
    process.env.MEMGUARD_BACKEND_URL = 'http://backend:8000'
    const rules = await nextConfig.rewrites!()

    expect(rules).toContainEqual({ source: '/api/:path*', destination: 'http://backend:8000/:path*' })
  })
})
