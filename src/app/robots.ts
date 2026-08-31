import type { MetadataRoute } from 'next'
import { SITE_URL } from '../lib/seo'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        // /booking is a multi-step inquiry funnel, not indexable content —
        // keep it out of search results the same way a checkout flow would be.
        disallow: ['/admin', '/api', '/booking'],
      },
      // Explicit block list for AI training/scraping agents.
      // Kept separate from the main "*" rule on purpose — a blanket
      // block on "*" would also take out Googlebot/Bingbot and defeat
      // the entire point of this build.
      { userAgent: 'GPTBot', disallow: '/' },
      { userAgent: 'CCBot', disallow: '/' },
      { userAgent: 'anthropic-ai', disallow: '/' },
      { userAgent: 'ClaudeBot', disallow: '/' },
      { userAgent: 'PerplexityBot', disallow: '/' },
      { userAgent: 'AhrefsBot', disallow: '/' },
      { userAgent: 'SemrushBot', disallow: '/' },
      { userAgent: 'MJ12bot', disallow: '/' },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  }
}
