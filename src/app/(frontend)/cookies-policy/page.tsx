import type { Metadata } from 'next'
import { getPayload } from '../../../lib/getPayload'
import { LegalPageView } from '../../../components/legal/LegalPageView'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Cookies Policy',
  description:
    'How Structured Adventures uses cookies and similar technologies on this site.',
}

async function getPage() {
  const payload = await getPayload()
  const result = await payload.find({
    collection: 'legal-pages',
    where: { slug: { equals: 'cookies-policy' } },
    limit: 1,
    depth: 1,
  })
  return result.docs[0] || null
}

export default async function CookiesPolicyPage() {
  const page = await getPage()
  return <LegalPageView page={page} />
}
