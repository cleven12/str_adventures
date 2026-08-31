import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getPayload } from '../../../../lib/getPayload'
import { mediaUrl } from '../../../../lib/media'
import { PageShell } from '../../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../../components/Breadcrumbs'
import { SectionHeading } from '../../../../components/SectionHeading'
import { TourCard } from '../../../../components/tours/TourCard'
import { ExploreMesh } from '../../../../components/ExploreMesh'

export const revalidate = 3600

async function getTopic(slug: string) {
  const payload = await getPayload()
  const tagRes = await payload.find({ collection: 'tags', where: { slug: { equals: slug } }, limit: 1 })
  const tag = tagRes.docs[0]
  if (!tag) return null

  const [tours, guides, articles, related] = await Promise.all([
    payload.find({ collection: 'tours', where: { tags: { in: [tag.id] } }, limit: 12, depth: 1 }),
    payload.find({ collection: 'guides', where: { tags: { in: [tag.id] } }, limit: 12, depth: 1 }),
    payload.find({ collection: 'articles', where: { tags: { in: [tag.id] } }, limit: 12, depth: 1 }),
    payload.find({
      collection: 'tags',
      where: { category: { equals: tag.category }, id: { not_equals: tag.id } },
      limit: 6,
    }),
  ])

  return { tag, tours: tours.docs, guides: guides.docs, articles: articles.docs, related: related.docs }
}

export default async function TopicHubPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const data = await getTopic(slug)
  if (!data) notFound()
  const { tag, tours, guides, articles, related } = data

  const hasContent = tours.length > 0 || guides.length > 0 || articles.length > 0

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={[tag.name]} />
        <div className="page-intro">
          <span className="eyebrow">Topic</span>
          <h1>{tag.name}</h1>
          {tag.description && <p>{tag.description}</p>}
        </div>

        {!hasContent && (
          <p className="muted">Nothing tagged with this topic yet.</p>
        )}

        {tours.length > 0 && (
          <section className="section" style={{ padding: '0 0 55px' }}>
            <SectionHeading eyebrow="Tours" title="Trips tagged with this topic" />
            <div className="tour-grid">
              {tours.map((t) => (
                <TourCard key={t.id} tour={t} />
              ))}
            </div>
          </section>
        )}

        {guides.length > 0 && (
          <section className="section" style={{ padding: '0 0 55px' }}>
            <SectionHeading eyebrow="Guides" title="Planning guides" />
            <div className="blog-grid">
              {guides.map((g) => (
                <Link className="blog-card" href={`/guides/${g.slug}`} key={g.id}>
                  <div
                    style={mediaUrl(g.heroImage) ? { backgroundImage: `url(${mediaUrl(g.heroImage)})` } : undefined}
                  />
                  <span className="eyebrow">{g.guideType === 'pillar' ? 'Pillar guide' : 'Guide'}</span>
                  <h2>{g.title}</h2>
                  <p>{g.excerpt || g.firstParagraph}</p>
                </Link>
              ))}
            </div>
          </section>
        )}

        {articles.length > 0 && (
          <section className="section" style={{ padding: '0 0 55px' }}>
            <SectionHeading eyebrow="Journal" title="Related stories" />
            <div className="blog-grid">
              {articles.map((a) => (
                <Link className="blog-card" href={`/blog/${a.slug}`} key={a.id}>
                  <div
                    style={mediaUrl(a.heroImage) ? { backgroundImage: `url(${mediaUrl(a.heroImage)})` } : undefined}
                  />
                  <span className="eyebrow">Journal</span>
                  <h2>{a.title}</h2>
                  <p>{a.excerpt || a.firstParagraph}</p>
                </Link>
              ))}
            </div>
          </section>
        )}

        {related.length > 0 && (
          <section className="related-section">
            <SectionHeading eyebrow="Keep exploring" title="Related topics" />
            <div className="topic-pills">
              {related.map((r) => (
                <Link className="topic-pill" href={`/topic/${r.slug}`} key={r.id}>
                  {r.name}
                </Link>
              ))}
            </div>
          </section>
        )}

        <ExploreMesh />
      </main>
    </PageShell>
  )
}
