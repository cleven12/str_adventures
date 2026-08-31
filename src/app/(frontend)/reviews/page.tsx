import type { Metadata } from 'next'
import Link from 'next/link'
import { Star } from 'lucide-react'
import { getPayload } from '../../../lib/getPayload'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { ExploreMesh } from '../../../components/ExploreMesh'
import type { Review, Tour } from '../../../payload-types'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Traveler Reviews',
  description: 'What travelers say about climbing Kilimanjaro and going on safari with Structured Adventures.',
}

async function getReviews() {
  const payload = await getPayload()
  const res = await payload.find({ collection: 'reviews', limit: 100, sort: '-reviewDate', depth: 1 })
  return res.docs
}

function Stars({ rating }: { rating: number }) {
  return (
    <div className="review-stars review-stars-dark" aria-label={`${rating} out of 5 stars`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star key={i} fill={i < rating ? '#c45121' : 'none'} />
      ))}
    </div>
  )
}

export default async function ReviewsPage() {
  const reviews = await getReviews()
  const average = reviews.length > 0 ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length : 0

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={['Reviews']} />
        <div className="center page-title">
          <span className="eyebrow">Traveler reviews</span>
          <h1>What it&apos;s actually like.</h1>
          {reviews.length > 0 && (
            <p>
              {average.toFixed(1)} average from {reviews.length} traveler{reviews.length === 1 ? '' : 's'} —
              collected directly, and from TripAdvisor and Google.
            </p>
          )}
        </div>

        {reviews.length === 0 && (
          <p className="muted center">
            No reviews published yet — add some in the CMS admin at <code>/admin/collections/reviews</code>.
          </p>
        )}

        <div className="review-grid">
          {reviews.map((review: Review) => {
            const tour = review.tour && typeof review.tour !== 'number' ? (review.tour as Tour) : null
            return (
              <article key={review.id} className="review-card review-card-light">
                <Stars rating={review.rating} />
                <p className="review-body">&ldquo;{review.body}&rdquo;</p>
                <div className="review-author">
                  <span>{review.authorName}</span>
                  {review.authorCountry && <span className="muted">{review.authorCountry}</span>}
                </div>
                {tour && (
                  <Link className="review-tour-link" href={`/tours/${tour.slug}`}>
                    On: {tour.title}
                  </Link>
                )}
              </article>
            )
          })}
        </div>
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
