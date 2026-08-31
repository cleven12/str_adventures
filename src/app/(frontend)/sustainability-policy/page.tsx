import type { Metadata } from 'next'
import { getPayload } from '../../../lib/getPayload'
import { LegalPageView } from '../../../components/legal/LegalPageView'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Sustainability Policy',
  description:
    'Our commitments to responsible tourism, local communities, and conservation in Tanzania.',
}

async function getPage() {
  const payload = await getPayload()
  const result = await payload.find({
    collection: 'legal-pages',
    where: { slug: { equals: 'sustainability-policy' } },
    limit: 1,
    depth: 1,
  })
  return result.docs[0] || null
}

export default async function SustainabilityPolicyPage() {
  const page = await getPage()
  return <LegalPageView page={page} />
}
