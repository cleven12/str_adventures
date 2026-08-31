import { getPayload } from 'payload'
import config from '../payload.config'

async function seed() {
  const payload = await getPayload({ config })

  const tagLemosho = await payload.create({
    collection: 'tags',
    data: { name: 'Lemosho Route', slug: 'lemosho-route', category: 'route' },
  })
  const tagJanuary = await payload.create({
    collection: 'tags',
    data: { name: 'Climbing in January', slug: 'climbing-in-january', category: 'season' },
  })
  const tagPrivate = await payload.create({
    collection: 'tags',
    data: { name: 'Private Groups', slug: 'private-groups', category: 'group-size' },
  })

  const category = await payload.create({
    collection: 'categories',
    data: { name: 'Kilimanjaro Treks', slug: 'kilimanjaro-treks', description: 'Guided ascents of Africa\u2019s highest peak.' },
  })

  const tour = await payload.create({
    collection: 'tours',
    data: {
      title: '8-Day Lemosho Route — Best Acclimatization Itinerary',
      slug: '8-day-lemosho-route',
      category: category.id,
      durationDays: 8,
      priceFrom: 2485,
      groupSize: { min: 1, max: 12 },
      firstParagraph:
        'The Lemosho Route is an 8-day Kilimanjaro trek starting from the west, offering the highest summit success rate of any route due to its gradual acclimatization profile.',
      tags: [tagLemosho.id, tagJanuary.id, tagPrivate.id],
      isActive: true,
      seoPriority: 0.9,
    },
  })

  await payload.create({
    collection: 'guides',
    data: {
      title: 'Complete Guide to Climbing Kilimanjaro',
      slug: 'complete-guide-climbing-kilimanjaro',
      guideType: 'pillar',
      primaryTour: tour.id,
      relatedTours: [tour.id],
      firstParagraph:
        'Everything you need to plan a Kilimanjaro climb: choosing a route, the best season, what it costs, and what to expect on summit night.',
      // Minimal lexical doc, loosely typed — this is placeholder seed content
      // (real content is authored via /admin's rich text editor).
      content: {
        root: {
          type: 'root',
          version: 1,
          direction: 'ltr',
          format: '',
          indent: 0,
          children: [
            {
              type: 'paragraph',
              version: 1,
              direction: 'ltr',
              format: '',
              indent: 0,
              children: [{ type: 'text', version: 1, text: 'Pillar content placeholder — replace via /admin.' }],
            },
          ],
        },
      } as any,
      tags: [tagLemosho.id, tagJanuary.id],
      isPublished: true,
      seoPriority: 1,
    },
  })

  await payload.create({
    collection: 'reviews',
    data: {
      authorName: 'Sarah',
      authorCountry: 'Australia',
      rating: 5,
      body: 'The guides knew the mountain inside and out. Summit night was brutal but the support made all the difference.',
      source: 'direct',
      tour: tour.id,
      isFeatured: true,
    },
  })

  console.log('Seed complete.')
  process.exit(0)
}

seed().catch((err) => {
  console.error(err)
  process.exit(1)
})
