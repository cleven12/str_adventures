import type { CollectionConfig } from 'payload'

export const Media: CollectionConfig = {
  slug: 'media',
  labels: { singular: 'Image', plural: 'Media Library' },
  admin: {
    description:
      'Every photo used anywhere on the site — Tour galleries, hero images, destination photos, etc. Upload here first, then pick the image when editing a Tour/Guide/Article/Destination.',
  },
  access: { read: () => true },
  upload: {
    // Actual storage target (Cloudinary) is wired in payload.config.ts
    // via src/lib/cloudinaryStorage.ts — gives image delivery a CDN with
    // automatic format/quality optimization instead of local disk.
    imageSizes: [
      { name: 'thumbnail', width: 400, height: 300, position: 'centre' },
      { name: 'card', width: 768, height: 512, position: 'centre' },
      { name: 'hero', width: 1600, height: 900, position: 'centre' },
    ],
    mimeTypes: ['image/*'],
  },
  fields: [
    {
      name: 'alt',
      type: 'text',
      required: true,
      admin: { description: 'Describe what\'s in the photo in a short sentence, e.g. "Sunrise over Uhuru Peak". Required for accessibility and helps image SEO — don\'t leave it generic.' },
    },
    { name: 'caption', type: 'text', admin: { description: 'Optional credit or caption, shown under the image if your page design displays one.' } },
  ],
}
