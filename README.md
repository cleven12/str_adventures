# Structured Adventures CMS

Headless Payload CMS + Next.js platform for Structured Adventures, a Tanzania
safari & Kilimanjaro tour operator — **Next.js 16 (App Router) + Payload
CMS 3, running as a single monolith deploy.** Payload is mounted directly
inside the Next.js app (no separate backend process, one repo, one process).

**Commerce is intentionally not implemented.** No payment gateway, no booking
state machine. `priceFrom` on a Tour is display copy; conversion happens
through the `/contact` and `/booking` inquiry forms (`@payloadcms/
plugin-form-builder`), not a checkout flow.

This project is open source and welcomes contributors — see
[`CONTRIBUTING.md`](CONTRIBUTING.md) for how to get set up, and the
[Issues tab](https://github.com/cleven12/str_adventures/issues) for open
work, including a production-readiness backlog described below.

## What's implemented

- **Catalog** — `Tours` (itinerary with day-by-day geo points, activities,
  accommodation, meals, FAQs), `Categories` (destinations)
- **Content** — `Guides` (pillar/cluster), `Articles`
- **Mesh** — `Tags` + `/topic/[slug]` hub pages (the actual SEO moat — every
  tagged Tour/Guide/Article surfaces there automatically), plus an
  `ExploreMesh` cross-link block on every page pointing at the two
  highest-selling product hubs
- **Product hubs** — `/climbing-kilimanjaro` and `/tanzania-safari` (flagship
  category pages: route/itinerary comparison table, aggregated FAQs, related
  guides/articles/reviews) and a generic `/destinations/[slug]` for every
  other `Category`, all sharing one `DestinationHubView` template
- **Trust** — `Reviews` (staff-curated, not a third-party plugin — imported
  from TripAdvisor/Google/direct and rendered via `ReviewsRail`), surfaced on
  the homepage, every hub page, and a dedicated `/reviews` index
- **Legal** — `LegalPages` collection (richtext, CMS-editable) backing
  `/terms-and-conditions`, `/cookies-policy`, `/privacy-policy`,
  `/refund-policy`, `/editorial-policy`, `/sustainability-policy`
- **Inquiries** — `plugin-form-builder`-backed, payment fields disabled;
  powers `/contact` and the multi-step `/booking` flow
- Shared SEO field contract (`src/lib/seoFields.ts`) across every content
  type: excerpt, focus keyword, meta title/description/canonical/OG image,
  and an editor-picked `schemaType` (TouristTrip/Article/FAQPage/
  LocalBusiness)
- `sitemap.xml` and `robots.txt` generated dynamically — topic hubs and every
  index page included, AI scrapers blocked without blocking search/social
  crawlers, `/booking` excluded as a non-indexable funnel
- JSON-LD structured data (`src/lib/seo.ts`) on Tour/Article/Guide detail
  pages and a site-wide `LocalBusiness` entity
- Design system: `.sa-root`-scoped plain CSS, Plus Jakarta Sans (display) /
  Instrument Sans (body) / IBM Plex Mono (data/price/dates), terracotta/
  deep-green/cream palette — crossfading multi-image hero (`HeroSlider`) on
  the homepage and both product hubs, a thin utility topbar (live star
  rating from `Reviews`, payment methods), a "Trusted & affiliated with"
  footer row (TATO / Tanzania Tourism Board / KPAP)
- MapLibre GL route map on Tour detail pages, driven by real itinerary geo
  data (no hardcoded points)
- Media storage: **Cloudinary** (`src/lib/cloudinaryStorage.ts`) — falls back
  to local disk if credentials are unset, safe for local dev without a
  Cloudinary account

## Local setup

```bash
cp .env.example .env       # fill in DATABASE_URI/PAYLOAD_SECRET for your machine
pnpm install
pnpm dev                   # http://localhost:3000
pnpm seed                  # optional demo content
```

Postgres is used for both dev and prod via `@payloadcms/db-postgres` — point
`DATABASE_URI` at a local Postgres role/db for dev (see `.env.example`).
MySQL is never used; it isn't an official Payload adapter.

Visit `/admin` to create your first user and manage content. Visit `/` for
the public site, `/topic/<slug>` after seeding to see the mesh hub in
action.

> **Known tooling issue:** `pnpm generate:types` and `pnpm seed` (both go
> through the `tsx` CLI) crash in some environments with
> `ERR_REQUIRE_ASYNC_MODULE` / "Cannot destructure loadEnvConfig" — an
> ESM/CJS interop bug between `tsx` and `@payloadcms/richtext-lexical`'s /
> Next's dist output, not caused by anything in this repo. `pnpm dev` and
> `next build`'s own TypeScript pass are unaffected (they use Next's own
> loader, not the `tsx` CLI). Workaround if you hit it: hand-edit
> `src/payload-types.ts` to match your schema change, and seed via the
> running dev server's REST API instead of `pnpm seed`. See open issue
> "Fix generate:types / pnpm seed tsx tooling crash".

## Commands

```bash
pnpm dev              # dev server
pnpm build             # production build — required green before shipping
pnpm lint              # eslint . (flat config, not `next lint`)
pnpm test              # vitest
pnpm generate:types    # after any collection/global field change (see tooling issue above)
pnpm seed              # demo content (src/lib/seed.ts)
```

## CI/CD

- **CI** (`.github/workflows/ci.yml`) runs on every push/PR: install, lint,
  `pnpm test`, then `pnpm build` against a real `postgres:16` service
  container (build-time static generation needs a live DB).
- **CD** (`.github/workflows/deploy.yml`) is a `workflow_dispatch`-only stub
  for an SSH-to-VPS-and-`pm2 reload` pipeline. **This is being retired, not
  activated** — see "Deploy target" below.

## Deploy target (in transition)

The original plan was a DigitalOcean VPS running Postgres + `pm2`. That VPS
is being retired and is not, and will not be, wired up. The next deploy
target is **Vercel (app) + Supabase (Postgres)**, tracked as an open
production-readiness issue — see the repo's Issues tab. Until that migration
lands, this repo has no live deployment; run it locally per "Local setup"
above.

**Do not put deploy credentials of any kind (SSH password, API token,
private key) directly in a workflow YAML file** — workflow files are plain
text in git history, and this is now a public repo. Use GitHub Actions
**encrypted secrets** (`Settings → Secrets and variables → Actions`) and
reference them as `${{ secrets.NAME }}`; for Vercel specifically, prefer
their native Git-integration deploys (no secrets in this repo at all) over a
custom Actions workflow where possible.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The open production-readiness
backlog (deploy migration, `generateStaticParams` on dynamic routes, a
working `/tours` filter panel, licensed photography to replace placeholder
imagery, an accessibility audit, and more) is tracked as labeled GitHub
Issues — good places to start.

## License

[GNU AGPL-3.0](LICENSE). You're free to use, study, modify, and
self-host this project — but if you run a modified version as a network
service (e.g. your own tour-operator site), you must make that modified
source available to your users under the same license. This keeps the
project and its improvements open, rather than allowing a closed-source
fork to compete against it.
