import type { Metadata } from 'next'
import { getPayload } from '../../../lib/getPayload'
import { LegalPageView } from '../../../components/legal/LegalPageView'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Editorial Policy',
  description:
    'How we research, write, and fact-check the guides and articles on this site.',
}

async function getPage() {
  const payload = await getPayload()
  const result = await payload.find({
    collection: 'legal-pages',
    where: { slug: { equals: 'editorial-policy' } },
    limit: 1,
    depth: 1,
  })
  return result.docs[0] || null
}

export default async function EditorialPolicyPage() {
  const page = await getPage()
  return <LegalPageView page={page} />
}
