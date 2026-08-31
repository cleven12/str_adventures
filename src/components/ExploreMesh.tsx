import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Reveal } from './motion/Reveal'

const links: [string, string, string][] = [
  ['Climbing Kilimanjaro', '/climbing-kilimanjaro', 'Six routes up Africa’s highest peak.'],
  ['Tanzania Safari', '/tanzania-safari', 'Serengeti, Ngorongoro & Tarangire.'],
  ['Day Trips', '/day-trips', 'One-day escapes from Moshi & Arusha.'],
  ['Destinations', '/destinations', 'Every region we run trips in.'],
  ['Guides & Stories', '/blog', 'Planning advice from the field.'],
  ['Traveler Reviews', '/reviews', 'What it’s actually like.'],
]

/** Cross-links to the site's core hub pages — the mesh that keeps every page one click from the top-selling products. */
export function ExploreMesh() {
  return (
    <Reveal>
      <section className="section explore-mesh">
        <div className="section-heading">
          <span className="eyebrow">Keep exploring</span>
          <h2>Everywhere else worth going.</h2>
        </div>
        <div className="explore-mesh-grid">
          {links.map(([label, href, copy]) => (
            <Link className="explore-mesh-item" href={href} key={href}>
              <span>{label}</span>
              <p>{copy}</p>
              <ArrowRight />
            </Link>
          ))}
        </div>
      </section>
    </Reveal>
  )
}
