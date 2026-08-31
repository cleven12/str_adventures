import type { Metadata } from 'next'
import type { Media, Tour } from '../payload-types'
import { mediaUrl } from './media'

export const SITE_URL = process.env.NEXT_PUBLIC_SERVER_URL || 'https://structuredadventures.com'
export const SITE_NAME = 'Structured Adventures'

type SeoDoc = {
  title: string
  metaTitle?: string | null
  metaDescription?: string | null
  excerpt?: string | null
  firstParagraph?: string | null
  canonicalUrl?: string | null
  ogImage?: (number | Media | null) | undefined
}

/** Shared `generateMetadata` builder for any content type carrying `seoFields`. */
export function buildMetadata(doc: SeoDoc, path: string): Metadata {
  const title = doc.metaTitle || doc.title
  const description = doc.metaDescription || doc.excerpt || doc.firstParagraph || undefined
  const url = doc.canonicalUrl || `${SITE_URL}${path}`
  const image = mediaUrl(doc.ogImage)

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      siteName: SITE_NAME,
      type: 'website',
      ...(image ? { images: [{ url: image }] } : {}),
    },
  }
}

type ArticleLikeDoc = SeoDoc & {
  schemaType?: string | null
  author?: string | null
  updatedAt: string
  createdAt: string
}

function articleJsonLd(doc: ArticleLikeDoc, path: string) {
  const image = mediaUrl(doc.ogImage)
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: doc.metaTitle || doc.title,
    description: doc.metaDescription || doc.excerpt || doc.firstParagraph || undefined,
    url: `${SITE_URL}${path}`,
    ...(image ? { image: [image] } : {}),
    datePublished: doc.createdAt,
    dateModified: doc.updatedAt,
    author: doc.author ? { '@type': 'Person', name: doc.author } : { '@type': 'Organization', name: SITE_NAME },
    publisher: { '@type': 'Organization', name: SITE_NAME, url: SITE_URL },
  }
}

function touristTripJsonLd(tour: Tour, path: string) {
  const image = mediaUrl(tour.ogImage) ?? mediaUrl(tour.gallery?.[0]?.image)
  return {
    '@context': 'https://schema.org',
    '@type': 'TouristTrip',
    name: tour.metaTitle || tour.title,
    description: tour.metaDescription || tour.excerpt || tour.firstParagraph || undefined,
    url: `${SITE_URL}${path}`,
    ...(image ? { image: [image] } : {}),
    ...(tour.durationDays ? { itinerary: `${tour.durationDays}-day itinerary` } : {}),
    ...(tour.priceFrom
      ? {
          offers: {
            '@type': 'Offer',
            priceCurrency: 'USD',
            price: tour.priceFrom,
            availability: 'https://schema.org/InStock',
          },
        }
      : {}),
    provider: { '@type': 'TravelAgency', name: SITE_NAME, url: SITE_URL },
  }
}

function faqPageJsonLd(faqs: { question: string; answer: string }[]) {
  if (faqs.length === 0) return null
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((f) => ({
      '@type': 'Question',
      name: f.question,
      acceptedAnswer: { '@type': 'Answer', text: f.answer },
    })),
  }
}

export function localBusinessJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    '@id': `${SITE_URL}/#business`,
    name: SITE_NAME,
    url: SITE_URL,
    description:
      'Structured Adventures — guided Kilimanjaro climbs, Tanzania safaris, and Zanzibar trip planning.',
  }
}

/**
 * Builds the JSON-LD graph for a Tour detail page: the editor-selected
 * `schemaType` as the primary entity, plus an always-on FAQPage entry when
 * the tour has FAQs (Google treats FAQPage as a supplementary schema, not
 * an alternative to the main entity type).
 */
export function tourJsonLd(tour: Tour, path: string) {
  const items: object[] = []
  if (tour.schemaType === 'TouristTrip') items.push(touristTripJsonLd(tour, path))
  else if (tour.schemaType === 'Article') items.push(articleJsonLd(tour, path))
  else if (tour.schemaType === 'LocalBusiness') items.push(localBusinessJsonLd())

  if (tour.faqs && tour.faqs.length > 0) {
    const faq = faqPageJsonLd(tour.faqs)
    if (faq) items.push(faq)
  }
  return items
}

/** Builds the JSON-LD graph for an Article/Guide detail page. */
export function articleLikeJsonLd(doc: ArticleLikeDoc, path: string) {
  const items: object[] = []
  if (doc.schemaType === 'Article') items.push(articleJsonLd(doc, path))
  else if (doc.schemaType === 'LocalBusiness') items.push(localBusinessJsonLd())
  return items
}
