import type { Metadata } from 'next'
import { cache } from 'react'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ChevronDown, Mountain } from 'lucide-react'
import { getPayload } from '../../../../lib/getPayload'
import { mediaUrl } from '../../../../lib/media'
import { PageShell } from '../../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../../components/Breadcrumbs'
import { SectionHeading } from '../../../../components/SectionHeading'
import { TourCard } from '../../../../components/tours/TourCard'
import { MapPanel, type ItineraryPoint } from '../../../../components/tours/MapPanel'
import { ExploreMesh } from '../../../../components/ExploreMesh'
import { JsonLd } from '../../../../components/JsonLd'
import { buildMetadata, tourJsonLd } from '../../../../lib/seo'
import type { Category, Tour } from '../../../../payload-types'

export const revalidate = 3600

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params
  const data = await getTour(slug)
  if (!data) return {}
  return buildMetadata(data.tour, `/tours/${slug}`)
}

const getTour = cache(async (slug: string) => {
  const payload = await getPayload()
  const res = await payload.find({ collection: 'tours', where: { slug: { equals: slug } }, limit: 1, depth: 2 })
  const tour = res.docs[0] as Tour | undefined
  if (!tour) return null

  const categoryId = tour.category && typeof tour.category !== 'number' ? tour.category.id : tour.category
  const related = await payload.find({
    collection: 'tours',
    where: {
      id: { not_equals: tour.id },
      isActive: { equals: true },
      ...(categoryId ? { category: { equals: categoryId } } : {}),
    },
    limit: 3,
    depth: 1,
  })

  return { tour, related: related.docs }
})

export default async function TourDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const data = await getTour(slug)
  if (!data) notFound()
  const { tour, related } = data

  const gallery = (tour.gallery ?? []).map((g) => mediaUrl(g.image)).filter(Boolean) as string[]
  const categoryDoc = tour.category && typeof tour.category !== 'number' ? (tour.category as Category) : null
  const category = categoryDoc?.name ?? null
  const points: ItineraryPoint[] = (tour.itinerary ?? [])
    .filter((day) => day.location?.lat != null && day.location?.lng != null)
    .map((day) => ({ day: day.day, lat: day.location!.lat as number, lng: day.location!.lng as number, name: day.location?.name }))

  return (
    <PageShell>
      <JsonLd data={tourJsonLd(tour, `/tours/${slug}`)} />
      <main className="page detail">
        <Breadcrumbs items={['Tours', tour.title]} />
        <div className="gallery">
          <div className="gallery-main" style={gallery[0] ? { backgroundImage: `url(${gallery[0]})` } : undefined}>
            {category && <span className="badge">{category}</span>}
          </div>
          <div className="gallery-side">
            {[gallery[1], gallery[2], gallery[3]].map((img, i) => (
              <div key={i} style={img ? { backgroundImage: `url(${img})` } : undefined} />
            ))}
          </div>
        </div>
        <div className="detail-layout">
          <section>
            <span className="eyebrow">
              {categoryDoc ? (
                <Link href={`/destinations/${categoryDoc.slug}`}>{categoryDoc.name}</Link>
              ) : (
                'Tour'
              )}
              {tour.durationDays ? ` · ${tour.durationDays} days` : ''}
            </span>
            <h1>{tour.title}</h1>

            {tour.itinerary && tour.itinerary.length > 0 && (
              <div className="itinerary">
                <h2>Itinerary overview</h2>
                {tour.itinerary.map((day, i) => (
                  <details key={day.id ?? day.day} open={i === 0}>
                    <summary>
                      <span>Day {day.day}</span>
                      {day.title}
                      <ChevronDown />
                    </summary>
                    {day.description && <p>{day.description}</p>}
                    {(day.activities?.length || day.accommodation || day.meals) && (
                      <ul>
                        {day.activities?.map((a) => <li key={a.id ?? a.activity}>{a.activity}</li>)}
                        {day.accommodation && <li>Accommodation: {day.accommodation}</li>}
                        {day.meals && <li>Meals: {day.meals}</li>}
                      </ul>
                    )}
                  </details>
                ))}
              </div>
            )}

            <MapPanel points={points} />

            {tour.faqs && tour.faqs.length > 0 && (
              <div className="itinerary">
                <h2>Frequently asked questions</h2>
                {tour.faqs.map((faq) => (
                  <details key={faq.id ?? faq.question}>
                    <summary>
                      <span>Q</span>
                      {faq.question}
                      <ChevronDown />
                    </summary>
                    <p>{faq.answer}</p>
                  </details>
                ))}
              </div>
            )}

            {related.length > 0 && (
              <section className="related-section">
                <SectionHeading eyebrow="Keep exploring" title="You might also like" />
                <div className="related-rail">
                  {related.map((t) => (
                    <TourCard key={t.id} tour={t} />
                  ))}
                </div>
              </section>
            )}
          </section>

          <aside className="booking-panel">
            <span>From</span>
            <strong>{tour.priceFrom ? `$${tour.priceFrom}` : 'On request'}</strong>
            <small>Per person</small>
            {tour.durationDays && (
              <div>
                <Mountain /> {tour.durationDays} days
              </div>
            )}
            {tour.groupSize?.max && (
              <div>
                <Mountain /> Max {tour.groupSize.max} guests
              </div>
            )}
            <Link className="button" href="/booking">
              Enquire now
            </Link>
            <p>No payment required · We reply within 24 hours</p>
          </aside>
        </div>
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
