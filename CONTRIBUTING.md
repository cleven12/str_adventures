# Contributing to Structured Adventures CMS

Thanks for considering a contribution. This is a Next.js 16 + Payload CMS 3
monolith (see `README.md` for the full feature list and architecture).

## Getting set up

```bash
cp .env.example .env       # fill in DATABASE_URI/PAYLOAD_SECRET for your machine
pnpm install
pnpm dev                   # http://localhost:3000, /admin for the CMS
pnpm seed                  # optional demo content
```

You'll need a local Postgres instance — see `.env.example` for the expected
`DATABASE_URI` shape. MySQL is never used; SQLite was removed in favor of
Postgres everywhere (dev and prod), matching Payload's officially supported
adapter.

If `pnpm generate:types` or `pnpm seed` crashes with
`ERR_REQUIRE_ASYNC_MODULE`, see the "Known tooling issue" note in
`README.md` — it's a `tsx`/ESM interop bug, not something you broke.

## Before opening a PR

```bash
pnpm lint    # eslint . (flat config, not `next lint`)
pnpm test    # vitest
pnpm build   # must be green — this is what CI checks
```

All three must pass. CI (`.github/workflows/ci.yml`) runs them automatically
against a real `postgres:16` service container on every push/PR.

## Where to start

Check the [Issues tab](https://github.com/cleven12/str_adventures/issues)
for open work, especially anything labeled `good first issue` or
`help wanted`. Most of the current backlog is production-readiness work
(SEO polish, accessibility, deploy migration) rather than new features —
see the issue list for the up-to-date picture.

If you want to propose something not already tracked as an issue, open one
first to discuss scope before sending a large PR.

## Conventions

- Branch off `main`, one focused change per PR.
- Keep commits scoped and messages descriptive of *why*, not just *what*.
- Match the existing patterns in the file/module you're touching (e.g. the
  shared `seoFields.ts` contract on every content collection, the
  `.sa-root`-scoped CSS system) rather than introducing a parallel approach.
- No commerce/payment code — this project deliberately routes conversion
  through inquiry forms, not a checkout flow (see `README.md`).

## License

By contributing, you agree your contributions are licensed under this
project's [AGPL-3.0 license](LICENSE).
