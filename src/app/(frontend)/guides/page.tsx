import Link from 'next/link'
import { getPayload } from '../../../lib/getPayload'
import { mediaUrl } from '../../../lib/media'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { ExploreMesh } from '../../../components/ExploreMesh'

export const revalidate = 3600

async function getGuides() {
  const payload = await getPayload()
  const res = await payload.find({
    collection: 'guides',
    where: { isPublished: { equals: true } },
    limit: 100,
    depth: 1,
  })
  return res.docs
}

export default async function GuidesPage() {
  const guides = await getGuides()

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={['Guides']} />
        <div className="page-intro">
          <span className="eyebrow">Plan with confidence</span>
          <h1>
            Route & trip
            <br />
            guides
          </h1>
          <p>In-depth planning guides for Kilimanjaro routes, safaris, and trip logistics.</p>
        </div>
        {guides.length === 0 && (
          <p className="muted">No guides published yet — add one in the CMS admin at <code>/admin</code>.</p>
        )}
        <div className="blog-grid">
          {guides.map((g) => (
            <Link className="blog-card" href={`/guides/${g.slug}`} key={g.id}>
              <div style={mediaUrl(g.heroImage) ? { backgroundImage: `url(${mediaUrl(g.heroImage)})` } : undefined} />
              <span className="eyebrow">{g.guideType === 'pillar' ? 'Pillar guide' : 'Guide'}</span>
              <h2>{g.title}</h2>
              <p>{g.excerpt || g.firstParagraph}</p>
            </Link>
          ))}
        </div>
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
