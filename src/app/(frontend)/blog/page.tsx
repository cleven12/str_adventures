import Link from 'next/link'
import { getPayload } from '../../../lib/getPayload'
import { mediaUrl } from '../../../lib/media'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { ExploreMesh } from '../../../components/ExploreMesh'

export const revalidate = 3600

async function getArticles() {
  const payload = await getPayload()
  const res = await payload.find({
    collection: 'articles',
    where: { isPublished: { equals: true } },
    limit: 100,
    depth: 1,
  })
  return res.docs
}

export default async function BlogPage() {
  const articles = await getArticles()

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={['Travel info']} />
        <div className="page-intro">
          <span className="eyebrow">From the field</span>
          <h1>
            Travel stories
            <br />& practical guides
          </h1>
        </div>
        {articles.length === 0 && (
          <p className="muted">No articles published yet — add one in the CMS admin at <code>/admin</code>.</p>
        )}
        <div className="blog-grid">
          {articles.map((a) => (
            <Link className="blog-card" href={`/blog/${a.slug}`} key={a.id}>
              <div style={mediaUrl(a.heroImage) ? { backgroundImage: `url(${mediaUrl(a.heroImage)})` } : undefined} />
              <span className="eyebrow">{a.author ? `By ${a.author}` : 'Journal'}</span>
              <h2>{a.title}</h2>
              <p>{a.excerpt || a.firstParagraph}</p>
            </Link>
          ))}
        </div>
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
