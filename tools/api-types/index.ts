// Type definitions for the Structured Adventures API (/api/v1/).
// Hand-written to match apps/*/serializers.py — copy into a frontend
// project's types/ folder, or `npm link` this package during development.

export interface ApiImage {
  url: string | null;
  alt: string;
}

export interface SchemaOrgBlock {
  "@context": string;
  "@type": string | string[];
  [key: string]: unknown;
}

export interface Seo {
  meta_title: string;
  meta_description: string;
  focus_keyword: string;
  secondary_keywords: string;
  canonical_url: string;
  og_title: string;
  og_description: string;
  og_image: string | null;
  twitter_card: string;
  schema_org: SchemaOrgBlock[];
}

export interface TagMini {
  id: number;
  name: string;
  slug: string;
}

export interface TourCategoryMini {
  id: number;
  name: string;
  slug: string;
}

export interface TourCard {
  id: number;
  title: string;
  slug: string;
  category: TourCategoryMini;
  tags: TagMini[];
  tour_type: string;
  difficulty: string;
  duration_days: number;
  place_name: string;
  price_usd: string;
  excerpt: string;
  is_featured: boolean;
  average_rating: number | null;
  review_count: number;
  feature_image: ApiImage | null;
  url: string;
}

export interface TourDetail {
  id: number;
  title: string;
  slug: string;
  category: TourCategoryMini;
  tags: TagMini[];
  tour_type: string;
  difficulty: string;
  duration_days: number;
  place_name: string;
  description: string;
  excerpt: string;
  pricing: {
    price_usd: string;
    final_price: string;
    discount_price: string | null;
    has_discount: boolean;
    deposit_amount: string;
    balance_due: string;
    currency: string;
  };
  images: {
    feature: ApiImage | null;
    og_image: ApiImage | null;
    gallery: ApiImage[];
  };
  reviews: {
    average_rating: number;
    total_count: number;
    verified_count: number;
    external_count: number;
  };
  related_content: {
    tours: TourCard[];
    guides: unknown[];
    articles: unknown[];
    destinations: unknown[];
    combos: unknown[];
  };
  seo: Seo;
  url: string;
}

export interface HomepageResponse {
  site: Record<string, unknown> | null;
  featured_tours: TourCard[];
  featured_combos: unknown[];
  featured_destinations: unknown[];
  group_departures: unknown[];
  reviews: unknown[];
  faqs: unknown[];
  featured_guides: unknown[];
  seo: { schema_org: SchemaOrgBlock[] };
}

export interface SearchResponse {
  q: string;
  total: number;
  results: {
    tours: TourCard[];
    guides: unknown[];
    articles: unknown[];
    destinations: unknown[];
  };
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
