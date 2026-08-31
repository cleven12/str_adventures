import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import type { Tour } from '../../payload-types'

/** Side-by-side route comparison — duration, price, group size — sorted shortest to longest. */
export function RouteCompareTable({ tours, title = 'Compare routes' }: { tours: Tour[]; title?: string }) {
  if (tours.length === 0) return null
  const sorted = [...tours].sort((a, b) => (a.durationDays ?? 99) - (b.durationDays ?? 99))

  return (
    <div className="route-compare">
      <h2>{title}</h2>
      <div className="route-compare-table">
        <div className="route-compare-row route-compare-head">
          <span>Route</span>
          <span>Duration</span>
          <span>Group size</span>
          <span>From</span>
          <span />
        </div>
        {sorted.map((tour) => (
          <Link className="route-compare-row" href={`/tours/${tour.slug}`} key={tour.id}>
            <span className="route-compare-name">{tour.title}</span>
            <span>{tour.durationDays ? `${tour.durationDays} days` : '—'}</span>
            <span>{tour.groupSize?.max ? `Up to ${tour.groupSize.max}` : 'Any size'}</span>
            <span>{tour.priceFrom ? `$${tour.priceFrom}` : 'On request'}</span>
            <span className="route-compare-cta">
              View <ArrowRight />
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
