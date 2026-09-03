// app/tours/[slug]/page.tsx
// Tour detail page — SSG with ISR every 30 minutes.
// Schema.org injected from API response — no manual schema needed.

import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getTour, getTourSlugs, SchemaOrgScripts } from "@/lib/api";

// ── Static params (called at build time) ──────────────────────────────────────

export async function generateStaticParams() {
  const slugs = await getTourSlugs();
  return slugs.map((slug) => ({ slug }));
}

// ── Metadata (SEO — called per page at build / ISR) ───────────────────────────

export async function generateMetadata(
  { params }: { params: Promise<{ slug: string }> }
): Promise<Metadata> {
  const { slug } = await params;

  try {
    const tour = await getTour(slug);
    const seo  = tour.seo;
    const img  = seo.og_image || tour.images.feature;

    return {
      title:       seo.meta_title,
      description: seo.meta_description,
      keywords:    [seo.focus_keyword, ...seo.secondary_keywords].filter(Boolean),
      alternates:  { canonical: seo.canonical_url },
      openGraph: {
        title:       seo.og_title || seo.meta_title,
        description: seo.og_description || seo.meta_description,
        url:         seo.canonical_url,
        type:        "website",
        images:      img ? [{ url: img.url, alt: img.alt }] : [],
      },
      twitter: {
        card:        seo.twitter_card as "summary_large_image",
        title:       seo.og_title || seo.meta_title,
        description: seo.og_description || seo.meta_description,
        images:      img ? [img.url] : [],
      },
    };
  } catch {
    return { title: "Tour Not Found" };
  }
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function TourDetailPage(
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;

  let tour;
  try {
    tour = await getTour(slug);
  } catch {
    notFound();
  }

  return (
    <>
      {/* Inject ALL schema.org from API — no manual JSON-LD needed */}
      <SchemaOrgScripts schemas={tour.seo.schema_org} />

      {/* Your tour detail UI components here */}
      <main>
        <h1>{tour.title}</h1>
        {/* ... */}
      </main>
    </>
  );
}

// Revalidate every 30 minutes (ISR)
export const revalidate = 1800;
