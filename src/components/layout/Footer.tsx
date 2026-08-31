import Link from 'next/link'
import { primaryNav } from './nav-data'

const PARTNERS = [
  'TATO — Tanzania Association of Tour Operators',
  'Tanzania Tourism Board',
  'KPAP — Kilimanjaro Porters Assistance Project',
]

export function Footer() {
  return (
    <>
      <div className="footer-partners">
        <span className="eyebrow">Trusted &amp; affiliated with</span>
        <div className="footer-partners-row">
          {PARTNERS.map((p) => (
            <span key={p}>{p}</span>
          ))}
        </div>
      </div>
      <footer>
      <div>
        <div className="brand footer-brand">
          <img
            src="https://structuredadventures.com/wp-content/uploads/2025/10/LOGO-STRUCTURED-ADVENTURES.png"
            alt="Structured Adventures"
            className="brand-logo"
          />
        </div>
        <p>Thoughtful travel, deeply rooted in place.</p>
        <div className="payment-badges">
          <span>VISA</span>
          <span>MC</span>
          <span>MPESA</span>
          <span>SSL</span>
        </div>
      </div>
      <div>
        <h4>Explore</h4>
        {primaryNav.slice(1, 5).map(([l, h]) => (
          <Link key={`${l}-${h}`} href={h}>
            {l}
          </Link>
        ))}
        <Link href="/reviews">Traveler Reviews</Link>
      </div>
      <div>
        <h4>Get in touch</h4>
        <span>Arusha, Tanzania</span>
        <span>+255 754 465 025</span>
        <span>info@structuredadventures.com</span>
      </div>
      <div>
        <h4>Legal</h4>
        <Link href="/terms-and-conditions">Terms &amp; Conditions</Link>
        <Link href="/cookies-policy">Cookies Policy</Link>
        <Link href="/privacy-policy">Privacy Policy</Link>
        <Link href="/refund-policy">Refund Policy</Link>
        <Link href="/editorial-policy">Editorial Policy</Link>
        <Link href="/sustainability-policy">Sustainability Policy</Link>
      </div>
      </footer>
    </>
  )
}
