import Link from 'next/link'
import { ArrowRight, CalendarDays, Compass, MapPin, Search, Users } from 'lucide-react'
import { getPayload } from '../../lib/getPayload'
import { mediaUrl } from '../../lib/media'
import { PageShell } from '../../components/layout/PageShell'
import { SectionHeading } from '../../components/SectionHeading'
import { TrustRow } from '../../components/TrustRow'
import { Certifications } from '../../components/Certifications'
import { TourCard } from '../../components/tours/TourCard'
import { ReviewsRail } from '../../components/reviews/ReviewsRail'
import { ExploreMesh } from '../../components/ExploreMesh'
import { Reveal } from '../../components/motion/Reveal'
import { HeroSlider } from '../../components/HeroSlider'

export const revalidate = 3600

// Crossfading hero slides — Kilimanjaro, safari, savanna sunset, Zanzibar coast.
// Used until an editor sets Settings.homeHeroImage in /admin, which is prepended
// as the first slide when present.
const HERO_SLIDES = [
  'https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?auto=format&fit=crop&w=1800&q=85',
  'https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?auto=format&fit=crop&w=1800&q=85',
  'https://images.unsplash.com/photo-1516493176284-cd5c4fd8b869?auto=format&fit=crop&w=1800&q=85',
  'https://images.unsplash.com/photo-1590523278191-995cbcda646b?auto=format&fit=crop&w=1800&q=85',
]

async function getHomeData() {
  const payload = await getPayload()
  const [tours, articles, categories, settings, reviews] = await Promise.all([
    payload.find({ collection: 'tours', limit: 6, where: { isActive: { equals: true } }, depth: 1 }),
    payload.find({ collection: 'articles', limit: 3, where: { isPublished: { equals: true } }, depth: 1 }),
    payload.find({ collection: 'categories', limit: 3, depth: 1 }),
    payload.findGlobal({ slug: 'settings', depth: 1 }),
    payload.find({ collection: 'reviews', limit: 3, where: { isFeatured: { equals: true } }, sort: '-reviewDate', depth: 0 }),
  ])
  return { tours: tours.docs, articles: articles.docs, categories: categories.docs, settings, reviews: reviews.docs }
}

export default async function HomePage() {
  const { tours, articles, categories, settings, reviews } = await getHomeData()
  const cmsHero = mediaUrl(settings.homeHeroImage)
  const heroSlides = cmsHero ? [cmsHero, ...HERO_SLIDES] : HERO_SLIDES

  return (
    <PageShell>
      <main>
        <section className="hero">
          <HeroSlider images={heroSlides} />
          <div className="scrim" />
          <div className="hero-copy">
            <span className="eyebrow light">Structured adventures</span>
            <h1>
              The adventure
              <br />
              <em>you&apos;ve been waiting for.</em>
            </h1>
            <p>
              From the mighty Kilimanjaro to the endless plains of the Serengeti, we&apos;ll take you deeper into
              Tanzania.
            </p>
            <Link className="button" href="/tours">
              Explore tours <ArrowRight />
            </Link>
          </div>
          <div className="search-bar">
            <label>
              <MapPin />
              Where to?
              <select>
                <option>Any destination</option>
                {categories.map((c) => (
                  <option key={c.id}>{c.name}</option>
                ))}
              </select>
            </label>
            <label>
              <Compass />
              Activity
              <select>
                <option>Any activity</option>
                <option>Climbing</option>
                <option>Safari</option>
              </select>
            </label>
            <label>
              <CalendarDays />
              Dates
              <input type="text" placeholder="Add dates" />
            </label>
            <label>
              <Users />
              Guests
              <input type="text" placeholder="Add guests" />
            </label>
            <button className="button">
              Search <Search />
            </button>
          </div>
        </section>

        <TrustRow />

        <Reveal>
          <section className="section intro-strip">
            <div>
              <span className="eyebrow">Travel differently</span>
              <h2>
                Wild places.
                <br />
                <em>Thoughtfully explored.</em>
              </h2>
            </div>
            <p>
              We design journeys with the people and landscapes of Tanzania at the heart of every detail. Go beyond
              the checklist with local guides, unhurried days, and routes that feel like your own.
            </p>
            <Link className="text-link" href="/about">
              Meet our team <ArrowRight />
            </Link>
          </section>
        </Reveal>

        <Reveal>
          <section className="section">
            <SectionHeading
              eyebrow="Explore Tanzania"
              title="Popular adventures"
              copy="Small groups, thoughtful routes, and a local perspective on the places that stay with you."
            />
            <div className="tour-grid">
              {tours.length === 0 && (
                <p className="muted">No tours published yet — add one in the CMS admin at <code>/admin</code>.</p>
              )}
              {tours.map((tour) => (
                <TourCard key={tour.id} tour={tour} />
              ))}
            </div>
            <div className="center">
              <Link className="button button-outline" href="/tours">
                View all adventures <ArrowRight />
              </Link>
            </div>
          </section>
        </Reveal>

        {categories.length > 0 && (
          <Reveal>
            <section className="section destination-preview">
              <SectionHeading eyebrow="Where will you go?" title="The places that stay with you." />
              <div className="preview-places">
                {categories.map((c) => (
                  <Link
                    href={`/destinations/${c.slug}`}
                    key={c.id}
                    className="preview-place"
                    style={mediaUrl(c.heroImage) ? { backgroundImage: `url(${mediaUrl(c.heroImage)})` } : undefined}
                  >
                    <span>{c.name}</span>
                    <ArrowRight />
                  </Link>
                ))}
              </div>
            </section>
          </Reveal>
        )}

        {articles.length > 0 && (
          <Reveal>
            <section className="section field-notes">
              <SectionHeading eyebrow="From the field" title="Notes for the journey." />
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
          </Reveal>
        )}

        <ReviewsRail reviews={reviews} />

        <ExploreMesh />

        <Certifications />
      </main>
    </PageShell>
  )
}
