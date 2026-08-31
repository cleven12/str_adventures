import type { Metadata } from 'next'
import { cache } from 'react'
import { notFound } from 'next/navigation'
import { getDestinationHubData } from '../../../../lib/destinationHub'
import { DestinationHubView } from '../../../../components/destinations/DestinationHubView'

export const revalidate = 3600

const getData = cache((slug: string) => getDestinationHubData(slug))

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params
  const data = await getData(slug)
  if (!data) return {}
  return {
    title: data.category.name,
    description: data.category.description || `Guided trips to ${data.category.name}, Tanzania.`,
  }
}

export default async function DestinationDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const data = await getData(slug)
  if (!data) notFound()

  return (
    <DestinationHubView
      category={data.category}
      eyebrow="Destination"
      intro={<p>{data.category.description || `Explore ${data.category.name} with a local team that knows it well.`}</p>}
      tours={data.tours}
      guides={data.guides}
      articles={data.articles}
      reviews={data.reviews}
      relatedTopics={data.relatedTopics}
    />
  )
}
