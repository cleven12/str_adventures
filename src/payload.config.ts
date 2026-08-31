import { postgresAdapter } from '@payloadcms/db-postgres'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import { buildConfig } from 'payload'
import sharp from 'sharp'
import path from 'path'
import { fileURLToPath } from 'url'

import { cloudinaryStorage } from './lib/cloudinaryStorage'
import { Tours } from './collections/Tours'
import { Categories } from './collections/Categories'
import { Guides } from './collections/Guides'
import { Articles } from './collections/Articles'
import { Tags } from './collections/Tags'
import { Reviews } from './collections/Reviews'
import { LegalPages } from './collections/LegalPages'
import { Media } from './collections/Media'
import { Users } from './collections/Users'
import { Inquiries } from './collections/Inquiries'
import { Settings } from './globals/Settings'

const filename = fileURLToPath(import.meta.url)
const dirname = path.dirname(filename)

/** Postgres everywhere — dev (local install) and prod (DigitalOcean VPS) both use it, no SQLite/MySQL. */
function getDatabaseAdapter() {
  const uri = process.env.DATABASE_URI
  if (!uri) {
    throw new Error('DATABASE_URI is required — see .env.example')
  }
  return postgresAdapter({
    pool: { connectionString: uri },
  })
}

export default buildConfig({
  serverURL: process.env.NEXT_PUBLIC_SERVER_URL || 'http://localhost:3000',
  admin: {
    user: Users.slug,
    meta: {
      titleSuffix: '— Structured Adventures CMS',
    },
  },
  editor: lexicalEditor(),
  // CATALOG (product) + CONTENT (marketing) + MESH (seo glue) + TRUST (reviews)
  // Commerce intentionally omitted — this build is catalog/content/demo only,
  // no booking flow, no payment processing.
  collections: [Tours, Categories, Guides, Articles, Tags, Reviews, LegalPages, Media, Users, Inquiries],
  globals: [Settings],
  typescript: {
    outputFile: path.resolve(dirname, 'payload-types.ts'),
  },
  db: getDatabaseAdapter(),
  secret: process.env.PAYLOAD_SECRET || '',
  sharp,
  plugins: [
    // Cloudinary is the Media CDN — auto format/quality delivery, off local
    // disk on the VPS. No-op (falls back to local disk) if credentials
    // aren't set, so local dev works without a Cloudinary account.
    cloudinaryStorage({
      cloudName: process.env.CLOUDINARY_CLOUD_NAME || '',
      apiKey: process.env.CLOUDINARY_API_KEY || '',
      apiSecret: process.env.CLOUDINARY_API_SECRET || '',
      folder: 'structured-adventures',
      enabled: Boolean(
        process.env.CLOUDINARY_CLOUD_NAME && process.env.CLOUDINARY_API_KEY && process.env.CLOUDINARY_API_SECRET,
      ),
    }),
  ],
})
