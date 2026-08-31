import type { MetadataRoute } from 'next'
import { getPayload } from '../lib/getPayload'
import { SITE_URL } from '../lib/seo'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const payload = await getPayload()

  const [tours, guides, articles, tags] = await Promise.all([
    payload.find({ collection: 'tours', limit: 1000, where: { isActive: { equals: true } } }),
    payload.find({ collection: 'guides', limit: 1000, where: { isPublished: { equals: true } } }),
    payload.find({ collection: 'articles', limit: 1000, where: { isPublished: { equals: true } } }),
    payload.find({ collection: 'tags', limit: 1000 }),
  ])

  const entries: MetadataRoute.Sitemap = [
    { url: SITE_URL, changeFrequency: 'weekly', priority: 1 },
    { url: `${SITE_URL}/tours`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE_URL}/day-trips`, changeFrequency: 'weekly', priority: 0.75 },
    { url: `${SITE_URL}/destinations`, changeFrequency: 'monthly', priority: 0.8 },
    { url: `${SITE_URL}/guides`, changeFrequency: 'weekly', priority: 0.7 },
    { url: `${SITE_URL}/blog`, changeFrequency: 'weekly', priority: 0.6 },
    { url: `${SITE_URL}/about`, changeFrequency: 'yearly', priority: 0.4 },
    { url: `${SITE_URL}/contact`, changeFrequency: 'yearly', priority: 0.4 },
    { url: `${SITE_URL}/terms`, changeFrequency: 'yearly', priority: 0.2 },
  ]

  for (const t of tours.docs) {
    entries.push({
      url: `${SITE_URL}/tours/${t.slug}`,
      lastModified: t.updatedAt,
      priority: t.seoPriority ?? 0.7,
    })
  }
  for (const g of guides.docs) {
    entries.push({
      url: `${SITE_URL}/guides/${g.slug}`,
      lastModified: g.updatedAt,
      priority: g.seoPriority ?? 0.6,
    })
  }
  for (const a of articles.docs) {
    entries.push({
      url: `${SITE_URL}/blog/${a.slug}`,
      lastModified: a.updatedAt,
      priority: a.seoPriority ?? 0.5,
    })
  }
  // Topic hub pages are the highest-leverage page type — don't let them
  // get forgotten in the sitemap the way most agency builds do.
  for (const t of tags.docs) {
    entries.push({ url: `${SITE_URL}/topic/${t.slug}`, priority: 0.8 })
  }

  return entries
}
