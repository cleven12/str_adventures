import Link from 'next/link'
import { PageShell } from '../layout/PageShell'
import { Breadcrumbs } from '../Breadcrumbs'
import { RichText } from '../RichText'
import { ExploreMesh } from '../ExploreMesh'
import type { LegalPage } from '../../payload-types'

const LEGAL_NAV: { slug: LegalPage['slug']; label: string; href: string }[] = [
  { slug: 'terms-and-conditions', label: 'Terms and Conditions', href: '/terms-and-conditions' },
  { slug: 'cookies-policy', label: 'Cookies Policy', href: '/cookies-policy' },
  { slug: 'privacy-policy', label: 'Privacy Policy', href: '/privacy-policy' },
  { slug: 'refund-policy', label: 'Refund Policy', href: '/refund-policy' },
  { slug: 'editorial-policy', label: 'Editorial Policy', href: '/editorial-policy' },
  { slug: 'sustainability-policy', label: 'Sustainability Policy', href: '/sustainability-policy' },
]

export function LegalPageView({ page }: { page: LegalPage | null }) {
  if (!page) {
    return (
      <PageShell>
        <main className="page legal-page">
          <Breadcrumbs items={['Legal']} />
          <div className="page-intro">
            <span className="eyebrow">Legal</span>
            <h1>Page not published yet</h1>
            <p>Add this policy in the CMS admin at <code>/admin/collections/legal-pages</code>.</p>
          </div>
        </main>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <main className="page legal-page">
        <Breadcrumbs items={[page.title]} />
        <div className="page-intro">
          <span className="eyebrow">Legal</span>
          <h1>{page.title}</h1>
          {page.summary && <p>{page.summary}</p>}
          <p>
            Last updated:{' '}
            {new Date(page.updatedAt).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        <div className="legal-layout">
          <nav className="legal-nav" aria-label="Legal pages">
            {LEGAL_NAV.map((item) => (
              <Link key={item.slug} href={item.href} aria-current={item.slug === page.slug ? 'page' : undefined}>
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="legal-content">
            <RichText data={page.content} />
          </div>
        </div>
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
