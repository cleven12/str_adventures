import type { Metadata } from 'next'
import { getPayload } from '../../../lib/getPayload'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { TourCard } from '../../../components/tours/TourCard'
import { ReviewsRail } from '../../../components/reviews/ReviewsRail'
import { ExploreMesh } from '../../../components/ExploreMesh'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Day Trips from Moshi & Arusha',
  description:
    'Half-day and full-day trips near Kilimanjaro — waterfalls, hot springs, Maasai culture, and crater lakes. No overnight stay required.',
}

async function getDayTrips() {
  const payload = await getPayload()
  const [tag, reviews] = await Promise.all([
    payload.find({ collection: 'tags', where: { slug: { equals: 'day-trips' } }, limit: 1 }),
    payload.find({ collection: 'reviews', where: { isFeatured: { equals: true } }, limit: 3, sort: '-reviewDate', depth: 0 }),
  ])
  if (tag.docs.length === 0) return { tours: [], reviews: reviews.docs }
  const tours = await payload.find({
    collection: 'tours',
    where: { and: [{ isActive: { equals: true } }, { tags: { in: [tag.docs[0].id] } }] },
    limit: 100,
    depth: 1,
  })
  return { tours: tours.docs, reviews: reviews.docs }
}

export default async function DayTripsPage() {
  const { tours, reviews } = await getDayTrips()

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={['Day Trips']} />
        <div className="page-intro">
          <span className="eyebrow">No overnight stay needed</span>
          <h1>
            Day trips from
            <br />
            Moshi & Arusha
          </h1>
          <p>Waterfalls, hot springs, Maasai culture, and crater lakes — half-day and full-day trips that fit around a climb or safari.</p>
        </div>
        <div className="listing-layout">
          <section className="results">
            <div className="results-head">
              <strong>{tours.length} day trips</strong>
            </div>
            {tours.length === 0 && (
              <p className="muted">No day trips published yet — add one in the CMS admin at <code>/admin</code>, tagged &quot;Day Trips&quot;.</p>
            )}
            {tours.map((tour) => (
              <TourCard key={tour.id} tour={tour} horizontal />
            ))}
          </section>
        </div>
        <ReviewsRail reviews={reviews} />
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
