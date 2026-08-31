import { getPayload } from './getPayload'

/** Shared data-fetch for any Category-driven hub page (destination detail, Kilimanjaro, Safari). */
export async function getDestinationHubData(categorySlug: string) {
  const payload = await getPayload()

  const categoryRes = await payload.find({
    collection: 'categories',
    where: { slug: { equals: categorySlug } },
    limit: 1,
    depth: 1,
  })
  const category = categoryRes.docs[0]
  if (!category) return null

  const toursRes = await payload.find({
    collection: 'tours',
    where: { category: { equals: category.id }, isActive: { equals: true } },
    limit: 24,
    depth: 1,
  })
  const tours = toursRes.docs
  const tourIds = tours.map((t) => t.id)

  const [guides, articles, reviews, relatedTopics] = await Promise.all([
    tourIds.length === 0
      ? Promise.resolve({ docs: [] })
      : payload.find({
          collection: 'guides',
          where: {
            or: [{ primaryTour: { in: tourIds } }, { relatedTours: { in: tourIds } }],
            isPublished: { equals: true },
          },
          limit: 6,
          depth: 1,
        }),
    tourIds.length === 0
      ? Promise.resolve({ docs: [] })
      : payload.find({
          collection: 'articles',
          where: { relatedTours: { in: tourIds }, isPublished: { equals: true } },
          limit: 6,
          depth: 1,
        }),
    payload.find({
      collection: 'reviews',
      where: tourIds.length === 0 ? {} : { or: [{ isFeatured: { equals: true } }, { tour: { in: tourIds } }] },
      limit: 6,
      sort: '-reviewDate',
      depth: 0,
    }),
    category.tags && category.tags.length > 0
      ? payload.find({
          collection: 'tags',
          where: {
            id: { in: (category.tags as (number | { id: number })[]).map((t) => (typeof t === 'number' ? t : t.id)) },
          },
          limit: 8,
        })
      : Promise.resolve({ docs: [] }),
  ])

  return {
    category,
    tours,
    guides: guides.docs,
    articles: articles.docs,
    reviews: reviews.docs,
    relatedTopics: relatedTopics.docs,
  }
}
