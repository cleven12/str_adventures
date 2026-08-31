import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { getDestinationHubData } from '../../../lib/destinationHub'
import { DestinationHubView } from '../../../components/destinations/DestinationHubView'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Climbing Kilimanjaro',
  description:
    'Guided Kilimanjaro climbs on Lemosho, Machame, and Rongai — compare routes, durations, and prices, then talk to a real guide.',
}

// Flagship product page — Kilimanjaro is one of the two highest-selling
// categories, so this gets bespoke intro copy and a route comparison table
// on top of the shared DestinationHubView sections.
export default async function ClimbingKilimanjaroPage() {
  const data = await getDestinationHubData('kilimanjaro')
  if (!data) notFound()

  return (
    <DestinationHubView
      category={data.category}
      breadcrumbLabel="Climbing Kilimanjaro"
      eyebrow="Africa's highest peak"
      extraHeroImages={[
        'https://images.unsplash.com/photo-1589553416260-f586c8f1514f?auto=format&fit=crop&w=1800&q=85',
        'https://images.unsplash.com/photo-1521651201144-634f700b36ef?auto=format&fit=crop&w=1800&q=85',
      ]}
      intro={
        <p>
          Six routes up the roof of Africa, each with its own character and acclimatization profile. We run small
          groups with local guides who know every camp, every ridge, and every shortcut to a stronger summit push.
        </p>
      }
      extraIntro={
        <>
          <div>
            <span className="eyebrow">Why climb with us</span>
            <h2>
              One mountain.
              <br />
              <em>No two climbs alike.</em>
            </h2>
          </div>
          <p>
            Route choice matters more than most climbers realize — it&apos;s the single biggest lever on your summit
            chances. Longer routes give your body more time to acclimatize; shorter ones suit strong hikers on a
            tighter schedule. We&apos;ll help you pick the right one for your fitness, dates, and budget.
          </p>
        </>
      }
      showRouteCompare
      tours={data.tours}
      guides={data.guides}
      articles={data.articles}
      reviews={data.reviews}
      relatedTopics={data.relatedTopics}
    />
  )
}
