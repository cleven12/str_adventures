import { getPayload } from '../../lib/getPayload'
import { mediaUrl } from '../../lib/media'
import { HeaderClient } from './HeaderClient'
import type { SearchGroup } from './SearchOverlay'

export async function Header() {
  const payload = await getPayload()
  const [tours, guides, destinations, reviews] = await Promise.all([
    payload.find({ collection: 'tours', limit: 6, where: { isActive: { equals: true } }, depth: 1 }),
    payload.find({ collection: 'guides', limit: 6, where: { isPublished: { equals: true } }, depth: 1 }),
    payload.find({ collection: 'categories', limit: 6, depth: 1 }),
    payload.find({ collection: 'reviews', limit: 500, depth: 0 }),
  ])

  const reviewSummary =
    reviews.docs.length > 0
      ? {
          count: reviews.totalDocs,
          average: reviews.docs.reduce((sum, r) => sum + r.rating, 0) / reviews.docs.length,
        }
      : null

  const searchGroups: SearchGroup[] = [
    {
      label: 'Tours',
      seeAllHref: '/tours',
      items: tours.docs.map((t) => ({ title: t.title, href: `/tours/${t.slug}`, image: mediaUrl(t.gallery?.[0]?.image) })),
    },
    {
      label: 'Destinations',
      seeAllHref: '/destinations',
      items: destinations.docs.map((c) => ({ title: c.name, href: '/destinations', image: mediaUrl(c.heroImage) })),
    },
    {
      label: 'Guides',
      seeAllHref: '/guides',
      items: guides.docs.map((g) => ({ title: g.title, href: `/guides/${g.slug}`, image: mediaUrl(g.heroImage) })),
    },
  ]

  return <HeaderClient searchGroups={searchGroups} reviewSummary={reviewSummary} />
}
