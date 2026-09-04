"""
Crazy SEO Engine for VISIT KILI ADVENTURES.

Central place for generating high-impact, Google-rich-result optimized structured data.

Designed to maximize value from content produced by:
- .claude/skills/seo-tour, seo-guide, seo-destination, seo-faq, seo-article
- JSON imports into Tour, Destination, TrekGuide, BlogArticle, FAQ
- Tag mesh + related content for topical authority

Key goals for crazy rankings:
- Full TouristTrip / TouristAttraction / FAQPage / HowTo / Article + Breadcrumb + Organization
- Automatic FAQ rich results from content_blocks (type=faq) and DestinationFAQ / global FAQ
- Complete Offer + AggregateRating + Itinerary where possible
- E-E-A-T signals (Organization with location in Moshi, authors)
- Compatible with Google Indexing API signals (fresh indexed + rich markup = faster ranking wins)
"""

import json
from datetime import datetime
from django.conf import settings
from django.utils.html import strip_tags
from django.urls import reverse


DOMAIN = getattr(settings, 'SITE_DOMAIN', 'visitkili.com')
BASE_URL = f"https://{DOMAIN}"
BRAND = getattr(settings, 'SITE_NAME', 'VISIT KILI ADVENTURES')
WHATSAPP = getattr(settings, 'WHATSAPP_NUMBER', '+255741788255')


def _abs(url_path: str) -> str:
    if url_path.startswith('http'):
        return url_path
    return f"{BASE_URL}{url_path}" if url_path.startswith('/') else f"{BASE_URL}/{url_path}"


def get_organization_schema() -> dict:
    """Global Organization + TravelAgency schema. Put this on almost every page."""
    org = {
        "@context": "https://schema.org",
        "@type": ["Organization", "TravelAgency"],
        "name": BRAND,
        "url": BASE_URL,
        "logo": "https://res.cloudinary.com/ducpxtvfj/image/upload/v1771429157/apple-icon-180x180_dc6jsh.png",
        "description": "Local Moshi-based tour operator specializing in Kilimanjaro climbs, Northern Tanzania safaris, Mount Meru, and Zanzibar beach extensions.",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Moshi",
            "addressRegion": "Kilimanjaro",
            "addressCountry": "TZ"
        },
        "areaServed": ["Tanzania", "Kilimanjaro", "Serengeti", "Ngorongoro", "Zanzibar"],
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": WHATSAPP,
            "contactType": "customer service",
            "availableLanguage": ["English", "Swahili"]
        },
        "sameAs": [
            "https://www.instagram.com/visitkili",
            "https://www.facebook.com/visitkili",
            f"https://wa.me/{WHATSAPP.replace('+','').replace(' ','')}"
        ]
    }
    return org


def get_website_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": BRAND,
        "url": BASE_URL,
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{BASE_URL}/tours/?q={{search_term_string}}",
            "query-input": "required name=search_term_string"
        }
    }


def get_breadcrumb_schema(breadcrumbs: list) -> dict:
    """
    breadcrumbs: list of dicts [{'name': '..', 'url': '/path-or-full'}]
    """
    items = []
    for idx, bc in enumerate(breadcrumbs, 1):
        url = _abs(bc.get('url', ''))
        items.append({
            "@type": "ListItem",
            "position": idx,
            "name": bc.get('name'),
            "item": url
        })
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }


def _extract_faqs_from_content_blocks(tour) -> list:
    """Leverage skills output: Tour.content_blocks of type 'faq' become rich FAQPage."""
    faqs = []
    if not hasattr(tour, 'content_blocks'):
        return faqs
    for block in tour.content_blocks.filter(block_type='faq').order_by('order'):
        if block.heading and block.content:
            faqs.append({
                "question": block.heading,
                "answer": strip_tags(block.content)
            })
    return faqs


def _build_itinerary_schema(tour, itinerary_items) -> dict | None:
    """Builds a simple ItemList itinerary when available (great for rich results)."""
    if not itinerary_items:
        return None
    elements = []
    for idx, item in enumerate(itinerary_items, 1):
        elements.append({
            "@type": "ListItem",
            "position": idx,
            "name": getattr(item, 'title', f"Day {getattr(item, 'day_number', idx)}"),
            "description": strip_tags(getattr(item, 'description', ''))[:280] or None
        })
    if not elements:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{tour.title} Itinerary",
        "itemListElement": elements
    }


def build_tour_schema(tour, request=None) -> list:
    """
    Produces a list of rich schema objects for a tour.
    Maximizes eligibility for:
    - Product / Offer rich results (price)
    - TouristTrip with itinerary
    - AggregateRating (from real reviews)
    - FAQPage (from imported content_blocks created by seo-tour skill)
    - Breadcrumbs

    The skills/seo-tour guarantee tight meta + faq blocks + related content.
    """
    schemas = []

    # 1. Organization on every entity page (helps E-E-A-T)
    schemas.append(get_organization_schema())

    # 2. Main entity - prefer TouristTrip for treks/safaris, fall back to Product
    schema_type = getattr(tour, 'schema_type', 'TouristTrip') or 'TouristTrip'
    main = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": tour.title,
        "description": tour.meta_description or tour.excerpt or strip_tags(tour.description)[:300],
        "url": _abs(tour.get_absolute_url()),
        "provider": {
            "@type": "Organization",
            "name": BRAND,
            "url": BASE_URL
        }
    }

    # Duration (ISO 8601 PxD format is powerful)
    if getattr(tour, 'duration_days', None):
        main["duration"] = f"P{tour.duration_days}D"

    # Place / location
    if getattr(tour, 'place_name', None):
        main["touristType"] = "Adventure travelers"
        main["location"] = {
            "@type": "Place",
            "name": tour.place_name
        }

    # Offers (critical for commercial intent pages)
    price = getattr(tour, 'final_price', None) or getattr(tour, 'price_usd', None)
    if price:
        main["offers"] = {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": _abs(tour.get_absolute_url()),
            "priceValidUntil": "2027-12-31"  # keep future for 2026/27 departures
        }

    # AggregateRating from annotated or related reviews
    avg = getattr(tour, 'average_rating', None) or getattr(tour, 'avg_rating', None)
    count = getattr(tour, 'total_reviews', None) or getattr(tour, 'review_count', None)
    if avg and count and int(count) > 0:
        main["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(round(float(avg), 1)),
            "reviewCount": str(count)
        }

    # Merge any extra structured_data from import (skills or manual)
    if getattr(tour, 'structured_data', None):
        try:
            extra = tour.structured_data if isinstance(tour.structured_data, dict) else json.loads(tour.structured_data)
            main.update(extra)
        except Exception:
            pass

    schemas.append(main)

    # 3. Breadcrumbs (always powerful)
    breadcrumbs = [
        {"name": "Home", "url": "/"},
        {"name": "Tours & Adventures", "url": "/tours/"},
        {"name": tour.title, "url": tour.get_absolute_url()}
    ]
    schemas.append(get_breadcrumb_schema(breadcrumbs))

    # 4. Itinerary as ItemList (when available)
    itinerary_items = []
    if hasattr(tour, 'itinerary') and tour.itinerary:
        itinerary_items = list(tour.itinerary.items.all().order_by('order', 'day_number')[:12])
    itin_schema = _build_itinerary_schema(tour, itinerary_items)
    if itin_schema:
        schemas.append(itin_schema)

    # 5. FAQPage from content_blocks (the magic from seo-tour skill + import)
    faq_list = _extract_faqs_from_content_blocks(tour)
    if faq_list:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": f["answer"]}
                } for f in faq_list[:12]  # avoid huge payloads
            ]
        }
        schemas.append(faq_schema)

    return schemas


def build_destination_schema(destination, request=None) -> list:
    """
    Rich schema for destination pages.
    Uses data from seo-destination skill imports (faqs list, related mesh, focus_keyword).
    """
    schemas = [get_organization_schema()]

    main = {
        "@context": "https://schema.org",
        "@type": "TouristAttraction",
        "name": destination.name,
        "description": destination.meta_description or destination.short_description,
        "url": _abs(destination.get_absolute_url()),
        "location": {
            "@type": "Place",
            "name": getattr(destination, 'location_name', destination.name)
        }
    }

    if getattr(destination, 'best_time_to_visit'):
        main["bestTimeToVisit"] = destination.best_time_to_visit

    schemas.append(main)

    # Breadcrumbs
    schemas.append(get_breadcrumb_schema([
        {"name": "Home", "url": "/"},
        {"name": "Destinations", "url": "/destinations/"},
        {"name": destination.name, "url": destination.get_absolute_url()}
    ]))

    # FAQPage from DestinationFAQ (populated by seo-destination JSON imports)
    if hasattr(destination, 'faqs') and destination.faqs.exists():
        faqs = [
            {"question": f.question, "answer": strip_tags(f.answer)}
            for f in destination.faqs.all()[:10]
        ]
        if faqs:
            schemas.append({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["answer"]}
                    } for f in faqs
                ]
            })

    return schemas


def build_faq_schema(faqs: list) -> dict:
    """Global or page-specific FAQPage. Reuses core.models logic + enhanced."""
    if not faqs:
        return {}
    main_entities = []
    for f in faqs:
        q = getattr(f, 'question', None) or f.get('question')
        a = getattr(f, 'answer', None) or f.get('answer')
        if q and a:
            main_entities.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": strip_tags(str(a))
                }
            })
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entities[:15]
    }


def build_guide_schema(guide, request=None) -> list:
    """For TrekGuide / BlogArticle. Respects schema_type chosen in seo-guide / seo-article."""
    schemas = [get_organization_schema()]

    schema_type = getattr(guide, 'schema_type', 'Article') or 'Article'
    main = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": guide.title,
        "description": getattr(guide, 'meta_description', None) or getattr(guide, 'excerpt', ''),
        "url": _abs(guide.get_absolute_url()),
        "author": {
            "@type": "Person",
            "name": "Visit Kili Local Experts"
        },
        "publisher": {
            "@type": "Organization",
            "name": BRAND,
            "url": BASE_URL
        }
    }

    if hasattr(guide, 'publish_date') and guide.publish_date:
        main["datePublished"] = guide.publish_date.isoformat()
    if hasattr(guide, 'updated_at'):
        main["dateModified"] = guide.updated_at.isoformat()

    schemas.append(main)

    # FAQ if the guide itself was created as FAQPage via skill
    if schema_type == 'FAQPage' and hasattr(guide, 'content_blocks'):
        faqs = _extract_faqs_from_content_blocks(guide)  # reuse works for guides too if they have blocks
        if faqs:
            schemas.append(build_faq_schema(faqs))

    return schemas


def render_schemas(schemas: list) -> str:
    """Return safe HTML block for multiple <script type="application/ld+json"> tags."""
    if not schemas:
        return ""
    blocks = []
    for s in schemas:
        try:
            blocks.append(
                f'<script type="application/ld+json">\n{json.dumps(s, ensure_ascii=False, indent=0)}\n</script>'
            )
        except Exception:
            continue
    return "\n".join(blocks)


# Convenience for views
def get_tour_schemas(tour, request) -> str:
    return render_schemas(build_tour_schema(tour, request))


def get_destination_schemas(destination, request) -> str:
    return render_schemas(build_destination_schema(destination, request))


def get_basic_meta(title: str, focus: str = "") -> dict:
    """Tiny helper returning base meta dict for quick use in views/services."""
    return {
        "title": title,
        "focus": focus or title,
    }
