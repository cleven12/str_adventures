import type { CollectionConfig } from 'payload'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import { slugField, seoFields } from '../lib/seoFields'

// CONTENT context — pillar/cluster hub-and-spoke pages (section 4.3 of the blueprint).
export const Guides: CollectionConfig = {
  slug: 'guides',
  admin: {
    useAsTitle: 'title',
    defaultColumns: ['title', 'guideType', 'isPublished', '_status'],
    description:
      'Long-form planning guides ("What to Pack for Kilimanjaro", "Best Time to Climb") — different from Articles, which are more like blog posts. Guides show up at /guides.',
  },
  versions: { drafts: { autosave: { interval: 2000 } }, maxPerDoc: 20 },
  access: { read: () => true },
  fields: [
    { name: 'title', type: 'text', required: true },
    slugField('title'),
    {
      name: 'guideType',
      type: 'select',
      options: [
        { label: 'Pillar', value: 'pillar' },
        { label: 'Cluster', value: 'cluster' },
      ],
      defaultValue: 'cluster',
      admin: {
        description:
          '"Pillar" = a comprehensive main guide on a topic (e.g. "Complete Guide to Climbing Kilimanjaro"). "Cluster" = a more specific guide that supports a pillar (e.g. "What to Pack"). Most guides are Cluster.',
      },
    },
    {
      name: 'primaryTour',
      type: 'relationship',
      relationTo: 'tours',
      admin: { description: 'The "book this" CTA target for this guide.' },
    },
    {
      name: 'relatedTours',
      type: 'relationship',
      relationTo: 'tours',
      hasMany: true,
      admin: { description: 'Other Tours worth linking to from this guide, shown in a "related" section.' },
    },
    {
      name: 'relatedGuides',
      type: 'relationship',
      relationTo: 'guides',
      hasMany: true,
      admin: { description: 'Other Guides worth linking to from this one.' },
    },
    { name: 'heroImage', type: 'upload', relationTo: 'media', admin: { description: 'Banner photo at the top of the guide.' } },
    { name: 'content', type: 'richText', editor: lexicalEditor(), required: true, admin: { description: 'The full guide body.' } },
    ...seoFields,
    { name: 'publishDate', type: 'date', admin: { position: 'sidebar', description: 'Shown as the publish date on the page, if your design displays one.' } },
    {
      name: 'isPublished',
      type: 'checkbox',
      defaultValue: false,
      admin: {
        position: 'sidebar',
        description: 'Must be checked for this guide to show up on the live site — separate from the Draft/Published status above.',
      },
    },
  ],
}
