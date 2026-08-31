import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { getPayload } from '../../../lib/getPayload'
import { mediaUrl } from '../../../lib/media'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { ExploreMesh } from '../../../components/ExploreMesh'

export const revalidate = 3600

async function getDestinations() {
  const payload = await getPayload()
  const res = await payload.find({ collection: 'categories', limit: 100, depth: 1 })
  return res.docs
}

export default async function DestinationsPage() {
  const destinations = await getDestinations()

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={['Destinations']} />
        <div className="center page-title">
          <span className="eyebrow">Explore Tanzania</span>
          <h1>Destinations</h1>
          <p>Escape to the familiar places Tanzania has to offer.</p>
        </div>
        {destinations.length === 0 && (
          <p className="muted center">No destinations published yet — add one in the CMS admin at <code>/admin</code>.</p>
        )}
        <div className="destination-grid">
          {destinations.map((d, i) => (
            <Link
              className={`destination-card d-${i}`}
              href={`/destinations/${d.slug}`}
              key={d.id}
              style={mediaUrl(d.heroImage) ? { backgroundImage: `url(${mediaUrl(d.heroImage)})` } : undefined}
            >
              <span>{d.name}</span>
              <ArrowRight />
            </Link>
          ))}
        </div>
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
