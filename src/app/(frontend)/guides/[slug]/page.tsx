import type { Metadata } from 'next'
import { cache } from 'react'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getPayload } from '../../../../lib/getPayload'
import { mediaUrl } from '../../../../lib/media'
import { PageShell } from '../../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../../components/Breadcrumbs'
import { RichText } from '../../../../components/RichText'
import { JsonLd } from '../../../../components/JsonLd'
import { SectionHeading } from '../../../../components/SectionHeading'
import { TourCard } from '../../../../components/tours/TourCard'
import { ExploreMesh } from '../../../../components/ExploreMesh'
import { articleLikeJsonLd, buildMetadata } from '../../../../lib/seo'
import type { Guide, Tour } from '../../../../payload-types'

export const revalidate = 3600

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params
  const guide = await getGuide(slug)
  if (!guide) return {}
  return buildMetadata(guide, `/guides/${slug}`)
}

const getGuide = cache(async (slug: string) => {
  const payload = await getPayload()
  const res = await payload.find({ collection: 'guides', where: { slug: { equals: slug } }, limit: 1, depth: 1 })
  return res.docs[0] ?? null
})

export default async function GuideDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const guide = await getGuide(slug)
  if (!guide) notFound()

  const relatedTours = [
    ...(guide.primaryTour && typeof guide.primaryTour !== 'number' ? [guide.primaryTour as Tour] : []),
    ...((guide.relatedTours ?? []).filter((t): t is Tour => typeof t !== 'number')),
  ].filter((t, i, arr) => arr.findIndex((o) => o.id === t.id) === i)
  const relatedGuides = (guide.relatedGuides ?? []).filter((g): g is Guide => typeof g !== 'number')

  return (
    <PageShell>
      <JsonLd data={articleLikeJsonLd(guide, `/guides/${slug}`)} />
      <article className="article page">
        <Breadcrumbs items={['Guides', guide.title]} />
        <div className="article-head">
          <span className="eyebrow">{guide.guideType === 'pillar' ? 'Pillar guide' : 'Guide'}</span>
          <h1>{guide.title}</h1>
        </div>
        {mediaUrl(guide.heroImage) && (
          <div className="article-image" style={{ backgroundImage: `url(${mediaUrl(guide.heroImage)})` }} />
        )}
        <div className="article-body">
          <p className="lead">{guide.firstParagraph}</p>
          <RichText data={guide.content} />
        </div>

        {relatedTours.length > 0 && (
          <section className="related-section">
            <SectionHeading eyebrow="Book this" title="Trips this guide covers" />
            <div className="tour-grid">
              {relatedTours.map((t) => (
                <TourCard key={t.id} tour={t} />
              ))}
            </div>
          </section>
        )}

        {relatedGuides.length > 0 && (
          <section className="related-guides">
            <SectionHeading eyebrow="Keep planning" title="Related guides" />
            <div className="topic-pills">
              {relatedGuides.map((g) => (
                <Link className="topic-pill" href={`/guides/${g.slug}`} key={g.id}>
                  {g.title}
                </Link>
              ))}
            </div>
          </section>
        )}

        <ExploreMesh />
      </article>
    </PageShell>
  )
}
