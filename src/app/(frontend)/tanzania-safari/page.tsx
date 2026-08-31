import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { getDestinationHubData } from '../../../lib/destinationHub'
import { DestinationHubView } from '../../../components/destinations/DestinationHubView'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Tanzania Safari',
  description:
    'Guided wildlife safaris across the Serengeti, Ngorongoro, and Tarangire — compare itineraries and talk to a local team.',
}

// Flagship product page — Safari is the other top-selling category
// alongside Kilimanjaro, so it gets the same bespoke treatment on top of
// the shared DestinationHubView sections.
export default async function TanzaniaSafariPage() {
  const data = await getDestinationHubData('serengeti')
  if (!data) notFound()

  return (
    <DestinationHubView
      category={data.category}
      breadcrumbLabel="Tanzania Safari"
      eyebrow="Wildlife, up close"
      extraHeroImages={[
        'https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?auto=format&fit=crop&w=1800&q=85',
        'https://images.unsplash.com/photo-1516426122078-c23e76319801?auto=format&fit=crop&w=1800&q=85',
      ]}
      intro={
        <p>
          The Serengeti, Ngorongoro Crater, and Tarangire in one trip — the Great Migration, the Big Five, and
          landscapes that don&apos;t look real until you&apos;re standing in them. Small groups, experienced
          driver-guides, and a pace that leaves room to actually watch the animals.
        </p>
      }
      extraIntro={
        <>
          <div>
            <span className="eyebrow">Why safari with us</span>
            <h2>
              Local guides.
              <br />
              <em>No rushed game drives.</em>
            </h2>
          </div>
          <p>
            Our driver-guides grew up around these parks — they read tracks, radio each other on sightings, and know
            which routes avoid the crowds. Every itinerary below can be adjusted for your dates, budget, and how much
            time you want in each park.
          </p>
        </>
      }
      showRouteCompare
      routeCompareTitle="Compare safari itineraries"
      tours={data.tours}
      guides={data.guides}
      articles={data.articles}
      reviews={data.reviews}
      relatedTopics={data.relatedTopics}
    />
  )
}
