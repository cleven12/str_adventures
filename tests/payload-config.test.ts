import { describe, expect, it } from 'vitest'

// DATABASE_URI must be set before importing payload.config — getDatabaseAdapter()
// throws otherwise. A real Postgres connection isn't needed for this test: the
// adapter is constructed lazily, not connected, at import time.
process.env.DATABASE_URI ||= 'postgres://test:test@localhost:5432/test'
process.env.PAYLOAD_SECRET ||= 'test-secret'

describe('payload.config', () => {
  it('registers every expected collection', async () => {
    const { default: config } = await import('../src/payload.config')
    const resolved = await config

    const slugs = resolved.collections?.map((c) => c.slug) ?? []
    for (const expected of ['articles', 'categories', 'guides', 'tours', 'inquiries', 'media', 'reviews', 'legal-pages', 'tags', 'users']) {
      expect(slugs).toContain(expected)
    }
  })
})
