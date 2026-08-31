import type { CollectionConfig } from 'payload'

// TRUST context. Manually curated / imported — never auto-solicited or
// incentivized inside this system. Review schema on tour pages reads
// from this collection's aggregate.
export const Reviews: CollectionConfig = {
  slug: 'reviews',
  admin: {
    useAsTitle: 'authorName',
    defaultColumns: ['authorName', 'rating', 'source', 'tour'],
    description:
      'Traveler reviews, entered by staff (not a public review form). Add these yourself from TripAdvisor, Google, or direct feedback — copy the review text over and set which Tour it\'s about.',
  },
  access: { read: () => true },
  fields: [
    { name: 'authorName', type: 'text', required: true, admin: { description: 'The reviewer\'s name, as it should display, e.g. "James T."' } },
    { name: 'authorCountry', type: 'text', admin: { description: 'Optional — e.g. "United Kingdom". Shown next to their name if set.' } },
    {
      name: 'rating',
      type: 'number',
      min: 1,
      max: 5,
      required: true,
      admin: { description: 'Star rating out of 5.' },
    },
    { name: 'body', type: 'textarea', required: true, admin: { description: 'The review text itself.' } },
    {
      name: 'source',
      type: 'select',
      options: ['direct', 'tripadvisor', 'google', 'safaribookings'],
      defaultValue: 'direct',
      required: true,
      admin: { description: 'Where this review came from — "direct" means it was sent to you personally, not pulled from another site.' },
    },
    { name: 'sourceUrl', type: 'text', admin: { description: 'Link to the original review, if imported.' } },
    {
      name: 'tour',
      type: 'relationship',
      relationTo: 'tours',
      admin: { description: 'Which Tour this review is about — leave blank for a general review not tied to one trip.' },
    },
    { name: 'reviewDate', type: 'date', admin: { description: 'When the review was originally written (not when you entered it here).' } },
    { name: 'isFeatured', type: 'checkbox', defaultValue: false, admin: { description: 'Highlight this review in featured/homepage review spots, if your page design uses one.' } },
  ],
}
