import { getPayload } from '../../../lib/getPayload'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { TourCard } from '../../../components/tours/TourCard'
import { ReviewsRail } from '../../../components/reviews/ReviewsRail'
import { ExploreMesh } from '../../../components/ExploreMesh'

export const revalidate = 3600

async function getTours() {
  const payload = await getPayload()
  const [tours, reviews] = await Promise.all([
    payload.find({ collection: 'tours', where: { isActive: { equals: true } }, limit: 100, depth: 1 }),
    payload.find({ collection: 'reviews', where: { isFeatured: { equals: true } }, limit: 3, sort: '-reviewDate', depth: 0 }),
  ])
  return { tours: tours.docs, reviews: reviews.docs }
}

export default async function ToursPage() {
  const { tours, reviews } = await getTours()

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={['Tours']} />
        <div className="page-intro">
          <span className="eyebrow">Find your route</span>
          <h1>
            Kilimanjaro climbs
            <br />& wildlife safaris
          </h1>
          <p>Choose your pace. We&apos;ll handle the details.</p>
        </div>
        <div className="listing-layout">
          <section className="results">
            <div className="results-head">
              <strong>{tours.length} adventures</strong>
            </div>
            {tours.length === 0 && (
              <p className="muted">No tours published yet — add one in the CMS admin at <code>/admin</code>.</p>
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
