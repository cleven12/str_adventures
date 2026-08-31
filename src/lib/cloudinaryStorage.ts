import { cloudStoragePlugin } from '@payloadcms/plugin-cloud-storage'
import type { Adapter } from '@payloadcms/plugin-cloud-storage/types'
import { v2 as cloudinary } from 'cloudinary'
import type { Plugin } from 'payload'

type CloudinaryStorageOptions = {
  cloudName: string
  apiKey: string
  apiSecret: string
  folder: string
  enabled: boolean
}

const stripExtension = (filename: string) => filename.replace(/\.[^./]+$/, '')

function createCloudinaryAdapter({ cloudName, apiKey, apiSecret, folder }: CloudinaryStorageOptions): Adapter {
  cloudinary.config({ cloud_name: cloudName, api_key: apiKey, api_secret: apiSecret, secure: true })

  const publicId = (filename: string) => `${folder}/${stripExtension(filename)}`
  const deliveryUrl = (filename: string) =>
    cloudinary.url(publicId(filename), { secure: true, fetch_format: 'auto', quality: 'auto' })

  return () => ({
    name: 'cloudinary',
    generateURL: ({ filename }) => deliveryUrl(filename),
    handleUpload: async ({ file }) => {
      await new Promise<void>((resolve, reject) => {
        const stream = cloudinary.uploader.upload_stream(
          { public_id: publicId(file.filename), resource_type: 'image', overwrite: true },
          (error) => (error ? reject(error) : resolve()),
        )
        stream.end(file.buffer)
      })
    },
    handleDelete: async ({ filename }) => {
      await cloudinary.uploader.destroy(publicId(filename), { resource_type: 'image' })
    },
    staticHandler: async (_req, { params: { filename } }) => Response.redirect(deliveryUrl(filename), 302),
  })
}

/**
 * Cloudinary as the Media collection's storage + image CDN — swaps out local
 * disk (and, on a VPS, avoids depending on Vercel Blob) for Cloudinary's
 * auto format/quality delivery. No-op (falls back to local disk) if
 * credentials aren't set, same convention as the plugin it replaces.
 */
export function cloudinaryStorage(options: CloudinaryStorageOptions): Plugin {
  return (incomingConfig) => {
    if (!options.enabled) return incomingConfig

    const adapter = createCloudinaryAdapter(options)
    const config = {
      ...incomingConfig,
      collections: (incomingConfig.collections || []).map((collection) => {
        if (collection.slug !== 'media') return collection
        return {
          ...collection,
          upload: {
            ...(typeof collection.upload === 'object' ? collection.upload : {}),
            disableLocalStorage: true,
          },
        }
      }),
    }

    return cloudStoragePlugin({
      collections: { media: { adapter } },
    })(config)
  }
}
