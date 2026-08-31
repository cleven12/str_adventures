import type { ReactNode } from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { mediaUrl } from '../../lib/media'
import { PageShell } from '../layout/PageShell'
import { Breadcrumbs } from '../Breadcrumbs'
import { SectionHeading } from '../SectionHeading'
import { Reveal } from '../motion/Reveal'
import { TourCard } from '../tours/TourCard'
import { RouteCompareTable } from '../tours/RouteCompareTable'
import { ReviewsRail } from '../reviews/ReviewsRail'
import { FaqList } from '../FaqList'
import { ExploreMesh } from '../ExploreMesh'
import { HeroSlider } from '../HeroSlider'
import type { Article, Category, Guide, Review, Tag, Tour } from '../../payload-types'

export function DestinationHubView({
  category,
  eyebrow,
  intro,
  extraIntro,
  extraHeroImages,
  tours,
  showRouteCompare = false,
  routeCompareTitle,
  guides,
  articles,
  reviews,
  relatedTopics,
  breadcrumbLabel,
}: {
  category: Category
  eyebrow: string
  intro: ReactNode
  extraIntro?: ReactNode
  /** Extra crossfade slides shown alongside the category's own hero image, if set. */
  extraHeroImages?: string[]
  tours: Tour[]
  showRouteCompare?: boolean
  routeCompareTitle?: string
  guides: Guide[]
  articles: Article[]
  reviews: Review[]
  relatedTopics: Tag[]
  breadcrumbLabel?: string
}) {
  const compareTitle = routeCompareTitle ?? `Choose your ${category.name} route`
  const heroImage = mediaUrl(category.heroImage)
  const heroSlides = [...(heroImage ? [heroImage] : []), ...(extraHeroImages ?? [])]
  const faqs = tours
    .flatMap((t) => t.faqs ?? [])
    .filter((faq, i, arr) => arr.findIndex((f) => f.question === faq.question) === i)
    .slice(0, 8)

  return (
    <PageShell>
      <main className="page">
        <Breadcrumbs items={[breadcrumbLabel ?? category.name]} />

        <section className="hero hub-hero">
          {heroSlides.length > 0 && <HeroSlider images={heroSlides} />}
          <div className="scrim" />
          <div className="hero-copy">
            <span className="eyebrow light">{eyebrow}</span>
            <h1>{category.name}</h1>
            {intro}
            <Link className="button" href="/booking">
              Plan this trip <ArrowRight />
            </Link>
          </div>
        </section>

        {extraIntro && (
          <Reveal>
            <section className="section intro-strip intro-strip-photo">
              {extraIntro}
              {extraHeroImages?.[0] && (
                <div className="intro-strip-image" style={{ backgroundImage: `url(${extraHeroImages[0]})` }} />
              )}
            </section>
          </Reveal>
        )}

        {showRouteCompare && tours.length > 1 && (
          <Reveal>
            <section className="section">
              <RouteCompareTable tours={tours} title={compareTitle} />
            </section>
          </Reveal>
        )}

        <Reveal>
          <section className="section">
            <SectionHeading
              eyebrow="Available now"
              title={`${category.name} trips`}
              copy={`${tours.length} guided ${tours.length === 1 ? 'itinerary' : 'itineraries'}, built around real routes and real dates.`}
            />
            {tours.length === 0 && <p className="muted">No trips published in this destination yet.</p>}
            <div className="tour-grid">
              {tours.map((t) => (
                <TourCard key={t.id} tour={t} />
              ))}
            </div>
          </section>
        </Reveal>

        {guides.length > 0 && (
          <Reveal>
            <section className="section field-notes">
              <SectionHeading eyebrow="Plan ahead" title="Guides for this trip" />
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
            </section>
          </Reveal>
        )}

        {faqs.length > 0 && (
          <Reveal>
            <section className="section">
              <SectionHeading eyebrow="Good to know" title="Frequently asked questions" />
              <FaqList items={faqs} />
            </section>
          </Reveal>
        )}

        <ReviewsRail reviews={reviews} />

        {articles.length > 0 && (
          <Reveal>
            <section className="section field-notes">
              <SectionHeading eyebrow="From the field" title="Stories from this destination" />
              <div className="blog-grid">
                {articles.map((a) => (
                  <Link className="blog-card" href={`/blog/${a.slug}`} key={a.id}>
                    <div style={mediaUrl(a.heroImage) ? { backgroundImage: `url(${mediaUrl(a.heroImage)})` } : undefined} />
                    <span className="eyebrow">Journal</span>
                    <h2>{a.title}</h2>
                    <p>{a.excerpt || a.firstParagraph}</p>
                  </Link>
                ))}
              </div>
            </section>
          </Reveal>
        )}

        {relatedTopics.length > 0 && (
          <Reveal>
            <section className="related-section">
              <SectionHeading eyebrow="Keep exploring" title="Related topics" />
              <div className="topic-pills">
                {relatedTopics.map((r) => (
                  <Link className="topic-pill" href={`/topic/${r.slug}`} key={r.id}>
                    {r.name}
                  </Link>
                ))}
              </div>
            </section>
          </Reveal>
        )}

        <ExploreMesh />

        <Reveal>
          <section className="section center cta-banner">
            <span className="eyebrow">Ready when you are</span>
            <h2>Talk to someone who&apos;s actually been there.</h2>
            <p>No payment online, no pressure — just a real conversation about dates, routes, and price.</p>
            <div className="cta-banner-actions">
              <Link className="button" href="/booking">
                Request a quote <ArrowRight />
              </Link>
              <Link className="button button-outline" href="/contact">
                Contact us
              </Link>
            </div>
          </section>
        </Reveal>
      </main>
    </PageShell>
  )
}
