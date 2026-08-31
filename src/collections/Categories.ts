import type { CollectionConfig } from 'payload'
import { slugField } from '../lib/seoFields'

// CATALOG context. A Category is a destination (Kilimanjaro, Serengeti,
// Zanzibar, ...) — every Tour belongs to exactly one, and the /destinations
// page lists these directly.
export const Categories: CollectionConfig = {
  slug: 'categories',
  labels: { singular: 'Destination', plural: 'Destinations' },
  admin: {
    useAsTitle: 'name',
    description:
      'A destination area, e.g. "Kilimanjaro" or "Zanzibar". Every Tour belongs to one of these, and they power the /destinations page.',
  },
  access: { read: () => true },
  fields: [
    { name: 'name', type: 'text', required: true, admin: { description: 'Shown as the destination name everywhere on the site, e.g. "Zanzibar".' } },
    slugField('name'),
    { name: 'description', type: 'textarea', admin: { description: 'A short paragraph about this destination. Optional — not shown everywhere, mainly for future use.' } },
    { name: 'heroImage', type: 'upload', relationTo: 'media', admin: { description: 'Background photo for this destination\'s card on the /destinations page.' } },
    {
      name: 'tags',
      type: 'relationship',
      relationTo: 'tags',
      hasMany: true,
      admin: { description: 'Optional — link this destination to related Topics for the mesh hub, if relevant.' },
    },
  ],
}
