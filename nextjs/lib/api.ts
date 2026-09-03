// lib/api.ts
// Single source of truth for all Django API calls in Next.js.
// Every function maps to one API endpoint.
// ISR revalidation times are tuned for a tour operator:
//   - Homepage/tours: 1800s (30 min) — content changes infrequently
//   - Search: no-cache — always fresh
//   - Static params: 3600s (1hr) — slugs rarely change

const API = process.env.NEXT_PUBLIC_DJANGO_API_URL || "http://localhost:8000";

// ── Generic fetch wrapper ───────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit & { revalidate?: number; tags?: string[] } = {}
): Promise<T> {
  const { revalidate = 1800, tags, ...rest } = options;

  const res = await fetch(`${API}/api/v1${path}`, {
    ...rest,
    headers: { "Content-Type": "application/json", ...rest.headers },
    next: { revalidate, ...(tags ? { tags } : {}) },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText} — ${path}`);
  }
  return res.json() as Promise<T>;
}

// ── Homepage ────────────────────────────────────────────────────────────────

export async function getHomepage() {
  return apiFetch<HomepageData>("/homepage/", { revalidate: 1800, tags: ["homepage"] });
}

// ── Tours ───────────────────────────────────────────────────────────────────

export async function getTourList(params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<TourListResponse>(`/tours/${qs}`, {
    revalidate: 1800,
    tags: ["tours"],
  });
}

export async function getTour(slug: string) {
  return apiFetch<TourDetail>(`/tours/${slug}/`, {
    revalidate: 1800,
    tags: [`tour-${slug}`],
  });
}

export async function getTourSlugs(): Promise<string[]> {
  return apiFetch<string[]>("/slugs/tours/", { revalidate: 3600 });
}

export async function getTourMeta() {
  return apiFetch<TourMeta>("/tours/meta/", { revalidate: 3600 });
}

// ── Tags ────────────────────────────────────────────────────────────────────

export async function getTagList() {
  return apiFetch<TagListResponse>("/tags/", { revalidate: 3600 });
}

export async function getTag(slug: string) {
  return apiFetch<TagDetail>(`/tags/${slug}/`, {
    revalidate: 1800,
    tags: [`tag-${slug}`],
  });
}

export async function getTagSlugs(): Promise<string[]> {
  return apiFetch<string[]>("/slugs/tags/", { revalidate: 3600 });
}

// ── Categories ──────────────────────────────────────────────────────────────

export async function getCategoryList() {
  return apiFetch<Category[]>("/categories/", { revalidate: 3600 });
}

export async function getCategory(slug: string) {
  return apiFetch<CategoryDetail>(`/categories/${slug}/`, { revalidate: 1800 });
}

// ── Combos ──────────────────────────────────────────────────────────────────

export async function getComboList() {
  return apiFetch<ComboCard[]>("/combos/", { revalidate: 1800 });
}

export async function getCombo(slug: string) {
  return apiFetch<ComboDetail>(`/combos/${slug}/`, { revalidate: 1800 });
}

export async function getComboSlugs(): Promise<string[]> {
  return apiFetch<string[]>("/slugs/combos/", { revalidate: 3600 });
}

// ── Guides ───────────────────────────────────────────────────────────────────

export async function getGuideList(params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<GuideListResponse>(`/guides/${qs}`, {
    revalidate: 1800,
    tags: ["guides"],
  });
}

export async function getGuide(slug: string) {
  return apiFetch<GuideDetail>(`/guides/${slug}/`, {
    revalidate: 1800,
    tags: [`guide-${slug}`],
  });
}

export async function getGuideSlugs(): Promise<string[]> {
  return apiFetch<string[]>("/slugs/guides/", { revalidate: 3600 });
}

// ── Articles ─────────────────────────────────────────────────────────────────

export async function getArticleList(params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<ArticleListResponse>(`/articles/${qs}`, { revalidate: 1800 });
}

export async function getArticle(slug: string) {
  return apiFetch<ArticleDetail>(`/articles/${slug}/`, {
    revalidate: 1800,
    tags: [`article-${slug}`],
  });
}

export async function getArticleSlugs(): Promise<string[]> {
  return apiFetch<string[]>("/slugs/articles/", { revalidate: 3600 });
}

// ── Destinations ──────────────────────────────────────────────────────────────

export async function getDestinationList(params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<DestinationListResponse>(`/destinations/${qs}`, { revalidate: 1800 });
}

export async function getDestination(slug: string) {
  return apiFetch<DestinationDetail>(`/destinations/${slug}/`, {
    revalidate: 1800,
    tags: [`destination-${slug}`],
  });
}

export async function getDestinationSlugs(): Promise<string[]> {
  return apiFetch<string[]>("/slugs/destinations/", { revalidate: 3600 });
}

// ── Reviews ───────────────────────────────────────────────────────────────────

export async function getReviews(params?: { tour?: string; source?: string }) {
  const qs = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
  return apiFetch<ReviewListResponse>(`/reviews/${qs}`, { revalidate: 3600 });
}

// ── Group Departures ──────────────────────────────────────────────────────────

export async function getGroupDepartures(params?: { tour?: string }) {
  const qs = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
  return apiFetch<GroupDepartureListResponse>(`/group-departures/${qs}`, { revalidate: 600 });
}

// ── FAQs ──────────────────────────────────────────────────────────────────────

export async function getFAQs() {
  return apiFetch<FAQListResponse>("/faqs/", { revalidate: 3600 });
}

// ── Search ────────────────────────────────────────────────────────────────────

export async function search(q: string) {
  if (!q || q.length < 2) return null;
  return apiFetch<SearchResponse>(`/search/?q=${encodeURIComponent(q)}`, {
    cache: "no-store", // search is always fresh
  });
}

// ── Site / Team / Careers ─────────────────────────────────────────────────────

export async function getSiteSettings() {
  return apiFetch<SiteSettings>("/site/", { revalidate: 3600 });
}

export async function getTeam() {
  return apiFetch<TeamMember[]>("/team/", { revalidate: 3600 });
}

export async function getCareers() {
  return apiFetch<JobPosting[]>("/careers/", { revalidate: 3600 });
}

// ── Schema.org injector ───────────────────────────────────────────────────────
// Use in page.tsx to inject JSON-LD from API response into <head>

export function SchemaOrgScripts({ schemas }: { schemas: object[] }) {
  return (
    <>
      {schemas.map((schema, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
      ))}
    </>
  );
}

// ── Types (minimal — expand as needed) ───────────────────────────────────────

export interface ImageField {
  url: string;
  alt: string;
}

export interface TagMini {
  id: number;
  name: string;
  slug: string;
  topic_pillar: string;
}

export interface CategoryMini {
  id: number;
  name: string;
  slug: string;
}

export interface TourCard {
  id: number;
  title: string;
  slug: string;
  category: CategoryMini;
  tags: TagMini[];
  tour_type: string;
  tour_type_label: string;
  difficulty: string;
  difficulty_label: string;
  duration_days: number;
  duration_label: string;
  place_name: string;
  price_usd: string;
  final_price: string;
  discount_price: string | null;
  excerpt: string;
  feature_image: ImageField | null;
  average_rating: number | null;
  total_reviews: number;
  is_featured: boolean;
  focus_keyword: string;
  best_months: number[];
  url: string;
}

export interface SEOData {
  meta_title: string;
  meta_description: string;
  focus_keyword: string;
  secondary_keywords: string[];
  canonical_url: string;
  og_title: string;
  og_description: string;
  og_image: ImageField | null;
  twitter_card: string;
  schema_org: object[];
}

export interface TourDetail extends TourCard {
  description: string;
  itinerary: ItineraryData | null;
  inclusions: Inclusion[];
  exclusions: Exclusion[];
  seasonal_windows: SeasonalWindow[];
  content_blocks: ContentBlock[];
  table_of_contents: TOCItem[];
  pricing: PricingData;
  images: { feature: ImageField | null; og_image: ImageField | null; gallery: GalleryImage[] };
  reviews: ReviewsData;
  group_departures: GroupDepartureCard[];
  availability: AvailabilitySlot[];
  related_content: RelatedContent;
  seo: SEOData;
}

export interface TourListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  filters_meta: FilterMeta;
  results: TourCard[];
  seo: { schema_org: object[] };
}

export interface HomepageData {
  site: SiteSettings | null;
  featured_tours: TourCard[];
  featured_combos: ComboCard[];
  featured_destinations: DestinationCard[];
  group_departures: GroupDepartureCard[];
  reviews: ExternalReview[];
  faqs: FAQ[];
  featured_guides: GuideCard[];
  seo: { schema_org: object[] };
}

export interface SearchResponse {
  q: string;
  total: number;
  results: {
    tours: TourCard[];
    guides: GuideCard[];
    articles: ArticleCard[];
    destinations: DestinationCard[];
  };
}

// Additional types abbreviated — add as needed
export interface ItineraryData { name: string; slug: string; days: ItineraryDay[] }
export interface ItineraryDay { day_number: number; title: string; description: string; altitude?: string; distance?: string; tags: TagMini[] }
export interface Inclusion { id: number; name: string; description: string; icon: string }
export interface Exclusion { id: number; name: string; description: string }
export interface SeasonalWindow { month_start: number; month_end: number; month_start_label: string; month_end_label: string; rating: string; rating_label: string; notes: string }
export interface ContentBlock { id: number; block_type: string; block_type_label: string; heading: string; content: string; content_plain: string; anchor_id: string; include_in_toc: boolean; focus_keyword: string; order: number }
export interface TOCItem { heading: string; anchor: string; level: string }
export interface PricingData { price_usd: string; final_price: string; discount_price: string | null; has_discount: boolean; savings: string | null; deposit_percentage: string; deposit_amount: string; balance_due: string; currency: string }
export interface GalleryImage { id: number; url: string; alt_text: string; caption: string; order: number; is_hero: boolean }
export interface ReviewsData { average_rating: number | null; total_count: number; verified_count: number; external_count: number; breakdown: Record<string, number>; breakdown_percent: Record<string, number>; verified: TourReview[]; external: ExternalReview[] }
export interface TourReview { id: number; name: string; rating: number; title: string; body: string; travel_date: string; is_verified: boolean; is_featured: boolean; admin_response: string; created_at: string }
export interface ExternalReview { id: number; source: string; source_label: string; reviewer_name: string; reviewer_location: string; reviewer_avatar: ImageField | null; rating: number; title: string; body: string; review_date: string; source_url: string; is_featured: boolean; tour_title: string | null; tour_slug: string | null }
export interface GroupDepartureCard { id: number; title: string; slug: string; tour: { title: string; slug: string; difficulty: string; difficulty_label: string; feature_image: ImageField | null; url: string }; start_date: string; end_date: string; price_per_person: string; capacity: number; current_count: number; spots_remaining: number; fill_percentage: number; status: string; status_label: string; feature_badge: string; feature_badge_label: string; urgency_label: string; has_reached_minimum: boolean; is_accepting_requests: boolean; days_until_departure: number; benefits_text: string; url: string }
export interface AvailabilitySlot { id: number; start_date: string; end_date: string; capacity: number; spots_remaining: number; status: string; effective_price: string }
export interface RelatedContent { tours: TourCard[]; guides: GuideCard[]; articles: ArticleCard[]; destinations: DestinationCard[]; combos: ComboCard[] }
export interface FilterMeta { categories: { slug: string; name: string; count: number }[]; price_range: { min: number; max: number }; duration_range: { min: number; max: number }; difficulties: string[]; tour_types: string[] }
export interface TourMeta { categories: CategoryMini[]; price_range: { min: number; max: number }; duration_range: { min: number; max: number }; difficulties: string[] }
export interface TagListResponse { grouped: Record<string, { id: number; name: string; slug: string; tour_count: number }[]>; flat: { id: number; name: string; slug: string; topic_pillar: string }[] }
export interface TagDetail { id: number; name: string; slug: string; topic_pillar: string; description: string; tours: TourCard[]; guides: GuideCard[]; articles: ArticleCard[]; seo: SEOData }
export interface Category { id: number; name: string; slug: string; description: string; tour_count: number; url: string }
export interface CategoryDetail extends Category { tours: TourCard[]; tours_count: number }
export interface ComboCard { id: number; title: string; slug: string; excerpt: string; total_price: string; duration_days: number; feature_image: ImageField | null; tours_included: string[]; url: string }
export interface ComboDetail extends ComboCard { tours: TourCard[]; savings: string | null; description: string; seo: SEOData }
export interface GuideCard { id: number; title: string; slug: string; category: CategoryMini; tags: TagMini[]; excerpt: string; first_paragraph: string; feature_image: ImageField | null; difficulty: string; reading_time: number; is_featured: boolean; publish_date: string; primary_tour: { title: string; slug: string; url: string } | null; author_name: string; focus_keyword: string; url: string }
export interface GuideDetail extends GuideCard { content: string; content_blocks: ContentBlock[]; table_of_contents: TOCItem[]; outgoing_links: InternalLink[]; related_tours: TourCard[]; related_articles: ArticleCard[]; nearby_guides: GuideCard[]; seo: SEOData }
export interface InternalLink { id: number; anchor_text: string; link_type: string; link_type_label: string; is_nofollow: boolean; resolved_url: string }
export interface ArticleCard extends GuideCard { status: string; published_at: string }
export interface ArticleDetail extends ArticleCard { content: string; related_tours: TourCard[]; related_guides: GuideCard[]; seo: SEOData }
export interface GuideListResponse { count: number; next: string | null; previous: string | null; results: GuideCard[] }
export interface ArticleListResponse { count: number; next: string | null; previous: string | null; results: ArticleCard[] }
export interface DestinationCard { id: number; name: string; slug: string; category: CategoryMini; short_description: string; feature_image: ImageField | null; is_featured: boolean; altitude: string; best_time_to_visit: string; focus_keyword: string; url: string }
export interface DestinationDetail extends DestinationCard { description: string; gallery: GalleryImage[]; faqs: FAQ[]; related_tours: TourCard[]; related_guides: GuideCard[]; related_articles: ArticleCard[]; tags: TagMini[]; seo: SEOData }
export interface DestinationListResponse { count: number; next: string | null; previous: string | null; results: DestinationCard[] }
export interface FAQ { id: number; question: string; answer: string; answer_plain: string; order: number }
export interface FAQListResponse { count: number; results: FAQ[]; seo: { schema_org: object[] } }
export interface ReviewListResponse { count: number; results: ExternalReview[] }
export interface GroupDepartureListResponse { count: number; results: GroupDepartureCard[] }
export interface SiteSettings { site_name: string; contact_email: string; contact_phone: string; whatsapp_number: string; office_address: string; show_announcement: boolean; announcement_text: string; announcement_link: string; holiday_mode: boolean; holiday_name: string; default_meta_title: string; default_meta_description: string; schema_org: object[] }
export interface TeamMember { id: number; name: string; role: string; bio: string; photo: ImageField | null; linkedin: string; years_experience: number; summits_count: number; order: number }
export interface JobPosting { id: number; title: string; slug: string; department: string; type: string; location: string; description: string; requirements: string; deadline: string | null; created_at: string; url: string }
