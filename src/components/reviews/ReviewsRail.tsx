import { Star } from 'lucide-react'
import { Reveal } from '../motion/Reveal'
import type { Review } from '../../payload-types'

function Stars({ rating }: { rating: number }) {
  return (
    <div className="review-stars" aria-label={`${rating} out of 5 stars`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star key={i} fill={i < rating ? '#c45121' : 'none'} />
      ))}
    </div>
  )
}

/** Reads directly from the Reviews collection — staff-curated, not a third-party plugin. */
export function ReviewsRail({ reviews }: { reviews: Review[] }) {
  if (reviews.length === 0) return null

  const average = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length

  return (
    <Reveal>
      <section className="section reviews-rail">
        <div className="section-heading reviews-rail-heading">
          <div>
            <span className="eyebrow">What travelers say</span>
            <h2>Trusted on the ground.</h2>
          </div>
          <div className="reviews-rail-average">
            <span className="reviews-rail-score">{average.toFixed(1)}</span>
            <div>
              <Stars rating={Math.round(average)} />
              <p className="muted">{reviews.length} traveler reviews</p>
            </div>
          </div>
        </div>
        <div className="reviews-rail-track">
          {reviews.map((review) => (
            <article key={review.id} className="review-card">
              <Stars rating={review.rating} />
              <p className="review-body">&ldquo;{review.body}&rdquo;</p>
              <div className="review-author">
                <span>{review.authorName}</span>
                {review.authorCountry && <span className="muted">{review.authorCountry}</span>}
              </div>
            </article>
          ))}
        </div>
      </section>
    </Reveal>
  )
}
