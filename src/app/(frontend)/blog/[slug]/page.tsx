import type { Metadata } from 'next'
import { cache } from 'react'
import { notFound } from 'next/navigation'
import { getPayload } from '../../../../lib/getPayload'
import { mediaUrl } from '../../../../lib/media'
import { PageShell } from '../../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../../components/Breadcrumbs'
import { RichText } from '../../../../components/RichText'
import { SectionHeading } from '../../../../components/SectionHeading'
import { TourCard } from '../../../../components/tours/TourCard'
import { ExploreMesh } from '../../../../components/ExploreMesh'
import { JsonLd } from '../../../../components/JsonLd'
import { articleLikeJsonLd, buildMetadata } from '../../../../lib/seo'
import type { Tour } from '../../../../payload-types'

export const revalidate = 3600

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params
  const data = await getArticle(slug)
  if (!data) return {}
  return buildMetadata(data.article, `/blog/${slug}`)
}

const getArticle = cache(async (slug: string) => {
  const payload = await getPayload()
  const res = await payload.find({ collection: 'articles', where: { slug: { equals: slug } }, limit: 1, depth: 1 })
  const article = res.docs[0]
  if (!article) return null

  const related = await payload.find({
    collection: 'articles',
    where: { id: { not_equals: article.id }, isPublished: { equals: true } },
    limit: 3,
    depth: 1,
  })

  return { article, related: related.docs }
})

export default async function ArticleDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const data = await getArticle(slug)
  if (!data) notFound()
  const { article, related } = data
  const relatedTours = (article.relatedTours ?? []).filter((t): t is Tour => typeof t !== 'number')

  return (
    <PageShell>
      <JsonLd data={articleLikeJsonLd(article, `/blog/${slug}`)} />
      <article className="article page">
        <Breadcrumbs items={['Travel info', article.title]} />
        <div className="article-head">
          <span className="eyebrow">{article.author ? `By ${article.author}` : 'Journal'}</span>
          <h1>{article.title}</h1>
          {article.publishDate && (
            <span className="mono">{new Date(article.publishDate).toLocaleDateString()}</span>
          )}
        </div>
        {mediaUrl(article.heroImage) && (
          <div className="article-image" style={{ backgroundImage: `url(${mediaUrl(article.heroImage)})` }} />
        )}
        <div className="article-body">
          <p className="lead">{article.firstParagraph}</p>
          <RichText data={article.content} />
        </div>

        {relatedTours.length > 0 && (
          <section className="related-section">
            <SectionHeading eyebrow="Book this" title="Trips mentioned in this story" />
            <div className="tour-grid">
              {relatedTours.map((t) => (
                <TourCard key={t.id} tour={t} />
              ))}
            </div>
          </section>
        )}

        {related.length > 0 && (
          <section className="related-guides">
            <SectionHeading eyebrow="More from the field" title="Keep reading" />
            <div className="blog-grid">
              {related.map((a) => (
                <a className="blog-card" href={`/blog/${a.slug}`} key={a.id}>
                  <div style={mediaUrl(a.heroImage) ? { backgroundImage: `url(${mediaUrl(a.heroImage)})` } : undefined} />
                  <span className="eyebrow">Journal</span>
                  <h2>{a.title}</h2>
                  <p>{a.excerpt || a.firstParagraph}</p>
                </a>
              ))}
            </div>
          </section>
        )}

        <ExploreMesh />
      </article>
    </PageShell>
  )
}
