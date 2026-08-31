import type { GlobalConfig } from 'payload'

// Site-wide content that doesn't belong to any single Tour/Guide/Article —
// currently just the homepage hero image. Admin-only writes since this
// affects branding sitewide, not routine per-page content.
export const Settings: GlobalConfig = {
  slug: 'settings',
  admin: {
    description:
      'Site-wide settings that affect the whole site, not one page — currently just the homepage hero photo. Only Admin accounts can change this.',
  },
  access: {
    read: ({ req }) => Boolean(req.user),
    update: ({ req }) => req.user?.role === 'admin',
  },
  fields: [
    {
      name: 'homeHeroImage',
      type: 'upload',
      relationTo: 'media',
      admin: {
        description: 'The large background photo behind the "The adventure you\'ve been waiting for" text on the homepage. Falls back to a stock photo until you set one.',
      },
    },
  ],
}
