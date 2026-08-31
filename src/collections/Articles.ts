import type { CollectionConfig } from 'payload'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import { slugField, seoFields } from '../lib/seoFields'

export const Articles: CollectionConfig = {
  slug: 'articles',
  admin: {
    useAsTitle: 'title',
    defaultColumns: ['title', 'author', 'isPublished', '_status'],
    description: 'Blog-style posts — trip stories, comparisons, news. Different from Guides, which are longer, more structured how-tos. Articles show up at /blog.',
  },
  versions: { drafts: { autosave: { interval: 2000 } }, maxPerDoc: 20 },
  access: { read: () => true },
  fields: [
    { name: 'title', type: 'text', required: true },
    slugField('title'),
    { name: 'author', type: 'text', admin: { description: 'Byline shown on the article, e.g. "Structured Adventures Team" or a person\'s name.' } },
    { name: 'heroImage', type: 'upload', relationTo: 'media', admin: { description: 'Banner photo at the top of the article.' } },
    { name: 'content', type: 'richText', editor: lexicalEditor(), required: true, admin: { description: 'The full article body.' } },
    {
      name: 'relatedTours',
      type: 'relationship',
      relationTo: 'tours',
      hasMany: true,
      admin: { description: 'Tours worth linking to from this article, shown in a "related" section.' },
    },
    {
      name: 'relatedGuides',
      type: 'relationship',
      relationTo: 'guides',
      hasMany: true,
      admin: { description: 'Guides worth linking to from this article.' },
    },
    ...seoFields,
    { name: 'publishDate', type: 'date', admin: { position: 'sidebar', description: 'Shown as the publish date on the page.' } },
    {
      name: 'isPublished',
      type: 'checkbox',
      defaultValue: false,
      admin: {
        position: 'sidebar',
        description: 'Must be checked for this article to show up on the live site — separate from the Draft/Published status above.',
      },
    },
  ],
}
