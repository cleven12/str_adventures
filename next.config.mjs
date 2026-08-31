import { withPayload } from '@payloadcms/next/withPayload'

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [{ hostname: '*.public.blob.vercel-storage.com' }],
  },
}

export default withPayload(nextConfig, { devBundleServerPackages: false })
