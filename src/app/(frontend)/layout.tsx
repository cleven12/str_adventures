import type { Metadata } from 'next'
import { Plus_Jakarta_Sans, Instrument_Sans, IBM_Plex_Mono } from 'next/font/google'
import { JsonLd } from '../../components/JsonLd'
import { localBusinessJsonLd, SITE_URL } from '../../lib/seo'
import './../../styles/globals.css'

// Kept the CSS variable name --font-fraunces (used ~50x across globals.css)
// but swapped the underlying face from a serif to a geometric sans — closer
// to the clean, fluid feel of Altezza Travel's Mazzard typeface, which we
// can't license directly.
const fraunces = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-fraunces',
  weight: ['500', '600', '700', '800'],
})

const instrument = Instrument_Sans({
  subsets: ['latin'],
  variable: '--font-instrument',
  weight: ['400', '500', '600'],
})

const plexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-plex-mono',
  weight: ['400', '500'],
})

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'Structured Adventures — Kilimanjaro Climbs & Tanzania Safaris',
    template: '%s · Structured Adventures',
  },
  description:
    'Guided Kilimanjaro climbs, Tanzania safaris, and Zanzibar trip planning — inquire directly, no payment required.',
}

export default function FrontendLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      className={`${fraunces.variable} ${instrument.variable} ${plexMono.variable}`}
    >
      <body>
        <JsonLd data={localBusinessJsonLd()} />
        {children}
      </body>
    </html>
  )
}
