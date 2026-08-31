'use client'

import Link from 'next/link'
import { ArrowRight, Heart } from 'lucide-react'
import type { Category, Tour } from '../../payload-types'
import { mediaUrl } from '../../lib/media'

export function TourCard({ tour, horizontal = false }: { tour: Tour; horizontal?: boolean }) {
  const image = mediaUrl(tour.gallery?.[0]?.image)
  const category = tour.category && typeof tour.category !== 'number' ? (tour.category as Category).name : null
  const teaser = tour.promoSubtitle

  return (
    <article className={`tour-card ${horizontal ? 'tour-horizontal' : ''}`}>
      <Link
        href={`/tours/${tour.slug}`}
        className="tour-image"
        style={image ? { backgroundImage: `url(${image})` } : undefined}
        aria-label={`View ${tour.title}`}
      >
        <div className="tour-image-tags">
          {category && <span className="badge">{category}</span>}
          {tour.durationDays && <span className="badge badge-muted">{tour.durationDays} days</span>}
        </div>
        <button aria-label="Save tour" onClick={(e) => e.preventDefault()}>
          <Heart />
        </button>
      </Link>
      <div className="tour-info">
        <h3>
          <Link href={`/tours/${tour.slug}`}>{tour.title}</Link>
        </h3>
        <p className="muted tour-teaser">
          {teaser || `Guided ${tour.durationDays ? `${tour.durationDays}-day` : ''} route with a local team.`}
        </p>
        <div className="tour-bottom">
          <span>
            From <strong>{tour.priceFrom ? `$${tour.priceFrom}` : 'request'}</strong>
          </span>
          <Link href={`/tours/${tour.slug}`} className="tour-view-link">
            View details <ArrowRight />
          </Link>
        </div>
      </div>
    </article>
  )
}
