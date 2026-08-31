import type { Field } from 'payload'

/**
 * The field contract from the architecture blueprint (section 3.3).
 * Every Listing / Guide / Article spreads this in. Keeping it in one
 * place is what lets the topic-hub template and schema renderer treat
 * all three content types identically.
 */
export const seoFields: Field[] = [
  {
    name: 'excerpt',
    type: 'textarea',
    maxLength: 300,
    admin: {
      description: '155–300 characters. Falls back to meta description if none is set below.',
    },
  },
  {
    name: 'firstParagraph',
    type: 'textarea',
    required: true,
    admin: {
      description:
        'Rendered prominently at the top of the page. This is the entity-context paragraph search engines read first to understand what the page is about — write it like a definition, not a hook.',
    },
  },
  {
    name: 'tags',
    type: 'relationship',
    relationTo: 'tags',
    hasMany: true,
    admin: {
      description: 'Drives the /topic/[slug] mesh hub — every tagged item surfaces there automatically.',
    },
  },
  {
    name: 'focusKeyword',
    type: 'text',
  },
  {
    name: 'secondaryKeywords',
    type: 'text',
    admin: {
      description: 'Comma-separated LSI terms.',
    },
  },
  {
    type: 'collapsible',
    label: 'Search & social metadata',
    fields: [
      { name: 'metaTitle', type: 'text' },
      { name: 'metaDescription', type: 'textarea', maxLength: 160 },
      { name: 'canonicalUrl', type: 'text' },
      { name: 'ogImage', type: 'upload', relationTo: 'media' },
      {
        name: 'schemaType',
        type: 'select',
        options: [
          { label: 'TouristTrip', value: 'TouristTrip' },
          { label: 'Article', value: 'Article' },
          { label: 'FAQPage', value: 'FAQPage' },
          { label: 'LocalBusiness', value: 'LocalBusiness' },
          { label: 'None', value: 'none' },
        ],
        defaultValue: 'none',
      },
    ],
  },
  {
    name: 'seoPriority',
    type: 'number',
    min: 0,
    max: 1,
    defaultValue: 0.5,
    admin: {
      step: 0.1,
      description: 'Sitemap priority weight (0–1).',
    },
  },
  {
    name: 'lastIndexedAt',
    type: 'date',
    admin: {
      readOnly: true,
      description: 'Set automatically when the search-engine ping job fires.',
    },
  },
]

export const slugField = (fromField = 'title'): Field => ({
  name: 'slug',
  type: 'text',
  required: true,
  unique: true,
  index: true,
  admin: {
    position: 'sidebar',
    description: `Permanent once published — never regenerate after indexing, even if ${fromField} changes.`,
  },
})
