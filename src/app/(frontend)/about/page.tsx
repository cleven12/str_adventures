import Link from 'next/link'
import { ArrowRight, Compass, Heart, Leaf, ShieldCheck } from 'lucide-react'
import { getPayload } from '../../../lib/getPayload'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { TrustRow } from '../../../components/TrustRow'
import { Certifications } from '../../../components/Certifications'
import { ReviewsRail } from '../../../components/reviews/ReviewsRail'
import { ExploreMesh } from '../../../components/ExploreMesh'

const values = [
  [Compass, 'Local experts'],
  [ShieldCheck, 'Safety first'],
  [Leaf, 'Responsible travel'],
  [Heart, 'Customer focused'],
] as const

export const revalidate = 3600

async function getReviews() {
  const payload = await getPayload()
  const res = await payload.find({ collection: 'reviews', where: { isFeatured: { equals: true } }, limit: 3, sort: '-reviewDate', depth: 0 })
  return res.docs
}

export default async function AboutPage() {
  const reviews = await getReviews()
  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={['About us']} />
        <section className="about-hero">
          <div>
            <span className="eyebrow">Our story</span>
            <h1>
              About Structured
              <br />
              <em>Adventures</em>
            </h1>
            <p>
              We are a 100% Tanzanian owned company based in Arusha, passionate about showing you the nature,
              beauty and culture of our country.
            </p>
            <p>
              With deep local roots and years of combined experience, our team creates responsible journeys that
              leave a positive mark.
            </p>
          </div>
          <div
            className="about-image"
            style={{
              backgroundImage:
                'url(https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?auto=format&fit=crop&w=1200&q=85)',
            }}
          />
        </section>
        <TrustRow />
        <section className="values">
          {values.map(([Icon, title]) => (
            <div key={title}>
              <Icon />
              <h3>{title}</h3>
              <p>Thoughtful details, handled by people who know Tanzania by heart.</p>
            </div>
          ))}
        </section>

        <section className="section intro-strip">
          <div>
            <span className="eyebrow">How we work</span>
            <h2>
              Small groups.
              <br />
              <em>No middlemen.</em>
            </h2>
          </div>
          <p>
            We run our own vehicles, work directly with mountain crews and driver-guides, and don&apos;t resell
            packages through third-party agents. That means fewer people between you and the trip, and a team that
            actually answers when something needs to change on the ground.
          </p>
          <Link className="text-link" href="/climbing-kilimanjaro">
            See how we run a Kilimanjaro climb <ArrowRight />
          </Link>
        </section>

        <ReviewsRail reviews={reviews} />
        <Certifications />
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
