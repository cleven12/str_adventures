import type { CollectionConfig } from 'payload'
import { lexicalEditor } from '@payloadcms/richtext-lexical'

// CONTENT context. Backs the fixed set of policy pages linked from the
// footer (Terms, Cookies, Privacy, Refund, Editorial, Sustainability).
// One doc per policy, identified by `slug` — the frontend route for each
// is hardcoded (so URLs stay stable) but the copy is fully editable here.
export const LegalPages: CollectionConfig = {
  slug: 'legal-pages',
  labels: { singular: 'Legal Page', plural: 'Legal Pages' },
  admin: {
    useAsTitle: 'title',
    defaultColumns: ['title', 'slug', 'updatedAt'],
    description:
      'The policy pages linked from the footer — Terms & Conditions, Cookies, Privacy, Refund, Editorial, and Sustainability. Edit the text here; each one has a fixed URL already wired up on the site.',
  },
  access: { read: () => true },
  fields: [
    { name: 'title', type: 'text', required: true, admin: { description: 'Page heading, e.g. "Privacy Policy".' } },
    {
      name: 'slug',
      type: 'select',
      required: true,
      unique: true,
      options: [
        { label: 'Terms and Conditions (/terms-and-conditions)', value: 'terms-and-conditions' },
        { label: 'Cookies Policy (/cookies-policy)', value: 'cookies-policy' },
        { label: 'Privacy Policy (/privacy-policy)', value: 'privacy-policy' },
        { label: 'Refund Policy (/refund-policy)', value: 'refund-policy' },
        { label: 'Editorial Policy (/editorial-policy)', value: 'editorial-policy' },
        { label: 'Sustainability Policy (/sustainability-policy)', value: 'sustainability-policy' },
      ],
      admin: { description: 'Which fixed policy URL this content fills in. Each value can only be used once.' },
    },
    {
      name: 'summary',
      type: 'textarea',
      admin: { description: 'Optional one-line summary shown under the title, e.g. what the policy covers.' },
    },
    { name: 'content', type: 'richText', editor: lexicalEditor(), required: true, admin: { description: 'The full policy text.' } },
  ],
}
