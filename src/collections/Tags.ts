import type { CollectionConfig } from 'payload'
import { slugField } from '../lib/seoFields'

export const Tags: CollectionConfig = {
  slug: 'tags',
  labels: { singular: 'Topic', plural: 'Topics' },
  admin: {
    useAsTitle: 'name',
    description:
      'Topics connect Tours, Guides, and Articles that share a theme (a route, a season, an activity...). Tag several items with the same Topic and they all show up together on that Topic\'s /topic/[slug] page — this is the main way the site builds internal links for SEO, so use it generously.',
  },
  access: { read: () => true },
  fields: [
    { name: 'name', type: 'text', required: true, admin: { description: 'Shown as the page title on this Topic\'s hub page, e.g. "Lemosho Route".' } },
    slugField('name'),
    { name: 'description', type: 'textarea', admin: { description: 'A sentence or two shown under the title on the Topic hub page.' } },
    {
      name: 'category',
      type: 'select',
      options: ['route', 'destination', 'season', 'activity', 'group-size', 'comparison'],
      admin: {
        description:
          'Groups this Topic with similar ones under "Related topics" on other hub pages. Pick whichever fits best — e.g. "Lemosho Route" is a route, "Climbing in January" is a season.',
      },
    },
  ],
}
