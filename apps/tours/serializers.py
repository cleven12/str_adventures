# apps/tours/serializers.py
# Every serializer here contributes to the SEO mesh.
# Tour detail is the richest response in the entire API —
# it includes related tours, guides, articles, destinations,
# combos, group departures, availability, content blocks,
# itinerary, reviews, and 4 pre-assembled schema.org objects.

from django.utils.html import strip_tags
from django.conf import settings
from rest_framework import serializers

from apps.tours.models import (
    Tag, TourCategory, Tour, TourImage,
    Itinerary, ItineraryItem, TourContentBlock,
    Inclusion, Exclusion, SeasonalWindow,
    TourAvailability, ComboPackage,
)
from apps.core.serializers import (
    SEOFieldsMixin, cloudinary_image_dict, secondary_keywords_list
)
from apps.core.seo_engine import (
    build_tour_schema,
    get_organization_schema,
    get_breadcrumb_schema,
    get_website_schema,
)

DOMAIN = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
BASE_URL = f"https://{DOMAIN}"

MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


# ── Tag ────────────────────────────────────────────────────────────────────────

class TagMiniSerializer(serializers.ModelSerializer):
    """Ultra-light tag — used inline in tour cards."""
    class Meta:
        model  = Tag
        fields = ["id", "name", "slug", "topic_pillar"]


class TagSerializer(serializers.ModelSerializer, SEOFieldsMixin):
    """Full tag serializer for tag landing pages (SEO mesh hub)."""
    url          = serializers.SerializerMethodField()
    tours        = serializers.SerializerMethodField()
    guides       = serializers.SerializerMethodField()
    articles     = serializers.SerializerMethodField()

    class Meta:
        model  = Tag
        fields = [
            "id", "name", "slug", "topic_pillar",
            "description", "meta_title", "meta_description",
            "is_active", "created_at",
            "url", "tours", "guides", "articles", "seo",
        ]

    def get_url(self, obj) -> str:
        return f"/tours/tag/{obj.slug}"

    def get_tours(self, obj) -> list:
        qs = (
            obj.tours
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags", "gallery")
            .order_by("-is_featured", "-created_at")[:12]
        )
        return TourCardSerializer(qs, many=True).data

    def get_guides(self, obj) -> list:
        from apps.guide.serializers import TrekGuideCardSerializer
        qs = (
            obj.trek_guides
            .filter(is_published=True)
            .select_related("category")
            .order_by("-publish_date")[:6]
        )
        return TrekGuideCardSerializer(qs, many=True).data

    def get_articles(self, obj) -> list:
        from apps.guide.serializers import BlogArticleCardSerializer
        qs = (
            obj.blog_articles
            .filter(status="published")
            .select_related("category")
            .order_by("-publish_date")[:6]
        )
        return BlogArticleCardSerializer(qs, many=True).data

    def get_seo_schemas(self, obj) -> list:
        return [
            get_organization_schema(),
            {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": f"{obj.name} Tours & Guides",
                "description": obj.meta_description or obj.description or f"All tours and guides about {obj.name} in Tanzania.",
                "url": f"{BASE_URL}/tours/tag/{obj.slug}",
                "about": {"@type": "Thing", "name": obj.name},
            },
            get_breadcrumb_schema([
                {"name": "Home",  "url": "/"},
                {"name": "Tours", "url": "/tours/"},
                {"name": obj.name, "url": f"/tours/tag/{obj.slug}"},
            ]),
        ]


# ── Category ───────────────────────────────────────────────────────────────────

class TourCategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TourCategory
        fields = ["id", "name", "slug"]


class TourCategorySerializer(serializers.ModelSerializer):
    tour_count = serializers.SerializerMethodField()
    url        = serializers.SerializerMethodField()

    class Meta:
        model  = TourCategory
        fields = [
            "id", "name", "slug", "description",
            "meta_title", "meta_description",
            "order", "tour_count", "url",
        ]

    def get_tour_count(self, obj) -> int:
        return obj.tours.filter(is_active=True).count()

    def get_url(self, obj) -> str:
        return f"/tours/category/{obj.slug}"


# ── Inclusion / Exclusion ──────────────────────────────────────────────────────

class InclusionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Inclusion
        fields = ["id", "name", "description", "icon"]


class ExclusionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Exclusion
        fields = ["id", "name", "description"]


# ── Itinerary ──────────────────────────────────────────────────────────────────

class ItineraryItemSerializer(serializers.ModelSerializer):
    tags = TagMiniSerializer(many=True, read_only=True)

    class Meta:
        model  = ItineraryItem
        fields = [
            "id", "day_number", "time", "title",
            "description", "order", "tags",
        ]


class ItinerarySerializer(serializers.ModelSerializer):
    days = serializers.SerializerMethodField()

    class Meta:
        model  = Itinerary
        fields = ["id", "name", "slug", "description", "days"]

    def get_days(self, obj) -> list:
        items = obj.items.all().prefetch_related("tags").order_by("order", "day_number")
        return ItineraryItemSerializer(items, many=True).data


# ── Seasonal Window ────────────────────────────────────────────────────────────

class SeasonalWindowSerializer(serializers.ModelSerializer):
    month_start_label = serializers.SerializerMethodField()
    month_end_label   = serializers.SerializerMethodField()
    rating_label      = serializers.SerializerMethodField()

    class Meta:
        model  = SeasonalWindow
        fields = [
            "id", "month_start", "month_end",
            "month_start_label", "month_end_label",
            "rating", "rating_label", "notes",
        ]

    def get_month_start_label(self, obj) -> str:
        return MONTH_NAMES[obj.month_start] if 1 <= obj.month_start <= 12 else ""

    def get_month_end_label(self, obj) -> str:
        return MONTH_NAMES[obj.month_end] if 1 <= obj.month_end <= 12 else ""

    def get_rating_label(self, obj) -> str:
        return obj.get_rating_display()


# ── Tour Content Block ─────────────────────────────────────────────────────────

class TourContentBlockSerializer(serializers.ModelSerializer):
    content_plain = serializers.SerializerMethodField()
    block_type_label = serializers.SerializerMethodField()

    class Meta:
        model  = TourContentBlock
        fields = [
            "id", "block_type", "block_type_label",
            "heading", "content", "content_plain",
            "anchor_id", "include_in_toc",
            "focus_keyword", "order",
        ]

    def get_content_plain(self, obj) -> str:
        return strip_tags(str(obj.content)) if obj.content else ""

    def get_block_type_label(self, obj) -> str:
        return obj.get_block_type_display()


# ── Gallery ────────────────────────────────────────────────────────────────────

class TourImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model  = TourImage
        fields = ["id", "url", "alt_text", "caption", "order", "is_hero"]

    def get_url(self, obj) -> str | None:
        try:
            return obj.image.url
        except Exception:
            return None


# ── Availability ───────────────────────────────────────────────────────────────

class TourAvailabilitySerializer(serializers.ModelSerializer):
    spots_remaining = serializers.IntegerField(read_only=True)
    is_available    = serializers.BooleanField(read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    fill_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model  = TourAvailability
        fields = [
            "id", "start_date", "end_date",
            "capacity", "booked_count", "spots_remaining",
            "fill_percentage", "is_available",
            "status", "effective_price",
        ]


# ── Tour Card (list view) ──────────────────────────────────────────────────────

class TourCardSerializer(serializers.ModelSerializer):
    """
    Lightweight tour card used in:
    - Homepage featured tours
    - Tour listing page
    - Related tours in other pages
    - Tag landing pages
    SEO: includes focus_keyword + tags for frontend to build rich anchors.
    """
    category       = TourCategoryMiniSerializer(read_only=True)
    tags           = TagMiniSerializer(many=True, read_only=True)
    feature_image  = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews  = serializers.SerializerMethodField()
    duration_label = serializers.SerializerMethodField()
    difficulty_label = serializers.SerializerMethodField()
    tour_type_label  = serializers.SerializerMethodField()
    final_price    = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    url            = serializers.SerializerMethodField()
    best_months    = serializers.SerializerMethodField()

    class Meta:
        model  = Tour
        fields = [
            "id", "title", "slug", "category", "tags",
            "tour_type", "tour_type_label",
            "difficulty", "difficulty_label",
            "duration_days", "duration_label",
            "place_name",
            "price_usd", "final_price", "discount_price",
            "deposit_percentage",
            "excerpt",
            "feature_image",
            "average_rating", "total_reviews",
            "is_featured",
            "focus_keyword",
            "best_months",
            "url",
        ]

    def get_feature_image(self, obj) -> dict | None:
        # First check gallery for is_hero image
        hero = None
        if hasattr(obj, '_prefetched_objects_cache') and 'gallery' in obj._prefetched_objects_cache:
            heroes = [i for i in obj.gallery.all() if i.is_hero]
            hero = heroes[0] if heroes else None
        if hero:
            return cloudinary_image_dict(hero.image, hero.alt_text or obj.title)
        return cloudinary_image_dict(obj.feature_image, obj.image_alt_text or obj.title)

    def get_average_rating(self, obj) -> float | None:
        # Use annotated value if available (from ViewSet annotation)
        v = getattr(obj, "avg_rating", None) or getattr(obj, "average_rating", None)
        return round(float(v), 1) if v else None

    def get_total_reviews(self, obj) -> int:
        v = getattr(obj, "review_count", None) or getattr(obj, "total_reviews", None)
        return int(v) if v else 0

    def get_duration_label(self, obj) -> str:
        n = obj.duration_days
        return f"{n} Day{'s' if n != 1 else ''}"

    def get_difficulty_label(self, obj) -> str:
        return obj.get_difficulty_display()

    def get_tour_type_label(self, obj) -> str:
        return obj.get_tour_type_display()

    def get_url(self, obj) -> str:
        return f"/tours/{obj.slug}"

    def get_best_months(self, obj) -> list[int]:
        """Return list of month numbers rated 'best' — used for UI badges."""
        months = []
        if hasattr(obj, '_prefetched_objects_cache') and 'seasonal_windows' in obj._prefetched_objects_cache:
            for sw in obj.seasonal_windows.all():
                if sw.rating == "best":
                    for m in range(sw.month_start, sw.month_end + 1):
                        if 1 <= m <= 12:
                            months.append(m)
        return sorted(set(months))


# ── Tour Detail (full) ─────────────────────────────────────────────────────────

class TourDetailSerializer(SEOFieldsMixin, serializers.ModelSerializer):
    """
    Full tour detail response.
    SEO: outputs 4 schema.org objects + full meta fields.
    Mesh: related_content links to guides, articles, destinations, combos.
    Frontend: everything needed to render the full tour detail page.
    """
    category         = TourCategorySerializer(read_only=True)
    tags             = TagMiniSerializer(many=True, read_only=True)
    itinerary        = ItinerarySerializer(read_only=True)
    inclusions       = InclusionSerializer(many=True, read_only=True)
    exclusions       = ExclusionSerializer(many=True, read_only=True)
    seasonal_windows = SeasonalWindowSerializer(many=True, read_only=True)
    content_blocks   = TourContentBlockSerializer(many=True, read_only=True)
    availability     = serializers.SerializerMethodField()
    images           = serializers.SerializerMethodField()
    reviews          = serializers.SerializerMethodField()
    group_departures = serializers.SerializerMethodField()
    related_content  = serializers.SerializerMethodField()
    table_of_contents = serializers.SerializerMethodField()
    pricing          = serializers.SerializerMethodField()
    tour_type_label  = serializers.SerializerMethodField()
    difficulty_label = serializers.SerializerMethodField()
    duration_label   = serializers.SerializerMethodField()
    average_rating   = serializers.SerializerMethodField()
    total_reviews    = serializers.SerializerMethodField()
    url              = serializers.SerializerMethodField()

    class Meta:
        model  = Tour
        fields = [
            # Core
            "id", "title", "slug",
            "category", "tags",
            "tour_type", "tour_type_label",
            "difficulty", "difficulty_label",
            "duration_days", "duration_label",
            "place_name", "max_altitude", "group_size",
            "target_audience", "lodge_level", "beach_type",
            # Content
            "description", "excerpt",
            # Structured content
            "itinerary", "inclusions", "exclusions",
            "seasonal_windows", "content_blocks",
            "table_of_contents",
            # Pricing
            "pricing",
            # Media
            "images",
            # Ratings
            "average_rating", "total_reviews", "reviews",
            # Status
            "is_featured", "page_views",
            # Availability
            "availability", "group_departures",
            # Mesh
            "related_content",
            # SEO (from SEOFieldsMixin)
            "seo",
            # URL
            "url",
        ]

    # ── Field methods ──────────────────────────────────────────────────────────

    def get_tour_type_label(self, obj) -> str:
        return obj.get_tour_type_display()

    def get_difficulty_label(self, obj) -> str:
        return obj.get_difficulty_display()

    def get_duration_label(self, obj) -> str:
        n = obj.duration_days
        return f"{n} Day{'s' if n != 1 else ''}"

    def get_average_rating(self, obj) -> float | None:
        v = getattr(obj, "avg_rating", None) or getattr(obj, "average_rating", None)
        return round(float(v), 1) if v else None

    def get_total_reviews(self, obj) -> int:
        v = getattr(obj, "review_count", None) or getattr(obj, "total_reviews", None)
        return int(v) if v else 0

    def get_url(self, obj) -> str:
        return f"/tours/{obj.slug}"

    def get_pricing(self, obj) -> dict:
        dep_pct  = float(obj.deposit_percentage)
        price    = float(obj.final_price)
        deposit  = round(price * dep_pct / 100, 2)
        return {
            "price_usd":          str(obj.price_usd),
            "final_price":        str(obj.final_price),
            "discount_price":     str(obj.discount_price) if obj.discount_price else None,
            "has_discount":       obj.discount_price is not None,
            "savings":            str(obj.price_usd - obj.discount_price) if obj.discount_price else None,
            "deposit_percentage": str(obj.deposit_percentage),
            "deposit_amount":     str(deposit),
            "balance_due":        str(round(price - deposit, 2)),
            "currency":           "USD",
        }

    def get_images(self, obj) -> dict:
        gallery = list(
            obj.gallery.all().order_by("order")
        )
        return {
            "feature": cloudinary_image_dict(
                obj.feature_image, obj.image_alt_text or obj.title
            ),
            "og_image": cloudinary_image_dict(obj.og_image),
            "gallery":  TourImageSerializer(gallery, many=True).data,
        }

    def get_table_of_contents(self, obj) -> list:
        """Build ToC from content blocks marked include_in_toc=True."""
        toc = []
        for block in obj.content_blocks.filter(
            include_in_toc=True,
            block_type__in=["heading", "subheading"],
        ).order_by("order"):
            if block.heading and block.anchor_id:
                toc.append({
                    "heading":  block.heading,
                    "anchor":   block.anchor_id,
                    "level":    "h2" if block.block_type == "heading" else "h3",
                })
        return toc

    def get_availability(self, obj) -> list:
        from django.utils import timezone
        qs = obj.availabilities.filter(
            status="open",
            start_date__gte=timezone.now()
        ).order_by("start_date")[:6]
        return TourAvailabilitySerializer(qs, many=True).data

    def get_group_departures(self, obj) -> list:
        from django.utils import timezone
        from apps.booking.serializers import GroupDepartureCardSerializer
        qs = obj.group_departures.filter(
            is_active=True,
            status__in=["open", "filling"],
            start_date__gte=timezone.now(),
        ).order_by("start_date")[:4]
        return GroupDepartureCardSerializer(qs, many=True).data

    def get_reviews(self, obj) -> dict:
        """
        Reviews with breakdown percentages.
        Returns both verified + external reviews for maximum social proof.
        """
        from apps.reviews.serializers import TourReviewSerializer, ExternalReviewSerializer

        verified = list(
            obj.tour_reviews.filter(is_approved=True)
            .select_related("booking")
            .order_by("-is_featured", "-created_at")[:8]
        )
        external = list(
            obj.external_reviews.filter(is_active=True)
            .order_by("order", "-review_date")[:4]
        )

        all_ratings = [r.rating for r in verified] + [r.rating for r in external]
        total = len(all_ratings)
        avg   = round(sum(all_ratings) / total, 1) if total else None

        breakdown = {str(i): 0 for i in range(5, 0, -1)}
        for r in all_ratings:
            breakdown[str(r)] = breakdown.get(str(r), 0) + 1

        breakdown_pct = {
            k: round(v / total * 100) if total else 0
            for k, v in breakdown.items()
        }

        return {
            "average_rating":    avg,
            "total_count":       total,
            "verified_count":    len(verified),
            "external_count":    len(external),
            "breakdown":         breakdown,
            "breakdown_percent": breakdown_pct,
            "verified":          TourReviewSerializer(verified, many=True).data,
            "external":          ExternalReviewSerializer(external, many=True).data,
        }

    def get_related_content(self, obj) -> dict:
        """
        The SEO mesh: every related entity linked back here.
        Frontend renders these as internal links → Google sees dense topical graph.
        """
        from apps.guide.serializers import TrekGuideCardSerializer, BlogArticleCardSerializer
        from apps.destinations.serializers import DestinationCardSerializer

        # Related tours: same category, same tags, excluding self
        related_tours = (
            Tour.objects
            .filter(is_active=True, category=obj.category)
            .exclude(pk=obj.pk)
            .select_related("category")
            .prefetch_related("tags", "gallery")
            .order_by("-is_featured")[:4]
        )
        # Also include tours sharing tags
        tag_ids = list(obj.tags.values_list("id", flat=True))
        related_pks = list(related_tours.values_list("pk", flat=True))
        if tag_ids:
            tag_tours = (
                Tour.objects
                .filter(is_active=True, tags__in=tag_ids)
                .exclude(pk=obj.pk)
                .exclude(pk__in=related_pks)
                .distinct()
                .select_related("category")
                .prefetch_related("tags", "gallery")[:2]
            )
        else:
            tag_tours = Tour.objects.none()

        all_related_tours = list(related_tours) + list(tag_tours)

        return {
            "tours": TourCardSerializer(all_related_tours[:5], many=True).data,
            "guides": TrekGuideCardSerializer(
                obj.related_guides.filter(is_published=True)
                .select_related("category")[:4],
                many=True,
            ).data,
            "articles": BlogArticleCardSerializer(
                obj.blog_articles.filter(status="published")
                .select_related("category")[:4],
                many=True,
            ).data,
            "destinations": DestinationCardSerializer(
                obj.mentioned_in_destinations.filter(is_active=True)[:3],
                many=True,
            ).data,
            "combos": ComboCardSerializer(
                obj.combo_packages.filter(is_active=True)[:2],
                many=True,
            ).data,
        }

    # ── SEO schema.org ────────────────────────────────────────────────────────

    def get_seo_schemas(self, obj) -> list:
        """
        Outputs 4 schema.org objects per tour:
        1. Organization (E-E-A-T signal)
        2. TouristTrip / Product (with Offer + AggregateRating)
        3. BreadcrumbList
        4. FAQPage (from content_blocks type=faq)
        5. ItemList itinerary (if available)
        """
        return build_tour_schema(obj, request=None)


# ── Combo Package ──────────────────────────────────────────────────────────────

class ComboCardSerializer(serializers.ModelSerializer):
    feature_image    = serializers.SerializerMethodField()
    tours_included   = serializers.SerializerMethodField()
    url              = serializers.SerializerMethodField()

    class Meta:
        model  = ComboPackage
        fields = [
            "id", "title", "slug", "excerpt",
            "total_price", "duration_days",
            "feature_image", "tours_included",
            "is_active", "url",
        ]

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(obj.featured_image, obj.title)

    def get_tours_included(self, obj) -> list[str]:
        return list(obj.tours.values_list("title", flat=True))

    def get_url(self, obj) -> str:
        return f"/combos/{obj.slug}"


class ComboDetailSerializer(SEOFieldsMixin, serializers.ModelSerializer):
    tours         = TourCardSerializer(many=True, read_only=True)
    tags          = TagMiniSerializer(many=True, read_only=True)
    feature_image = serializers.SerializerMethodField()
    savings       = serializers.SerializerMethodField()
    url           = serializers.SerializerMethodField()

    class Meta:
        model  = ComboPackage
        fields = [
            "id", "title", "slug", "description", "excerpt",
            "tours", "tags",
            "total_price", "duration_days",
            "feature_image", "savings",
            "is_active", "created_at",
            "url", "seo",
        ]

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(obj.featured_image, obj.title)

    def get_savings(self, obj) -> str | None:
        s = obj.savings_amount
        return str(s) if s else None

    def get_url(self, obj) -> str:
        return f"/combos/{obj.slug}"

    def get_seo_schemas(self, obj) -> list:
        return [
            get_organization_schema(),
            {
                "@context": "https://schema.org",
                "@type": "TouristTrip",
                "name": obj.title,
                "description": obj.meta_description or obj.excerpt,
                "url": f"{BASE_URL}/combos/{obj.slug}",
                "offers": {
                    "@type": "Offer",
                    "price": str(obj.total_price),
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock",
                },
            },
            get_breadcrumb_schema([
                {"name": "Home", "url": "/"},
                {"name": "Combo Packages", "url": "/combos/"},
                {"name": obj.title, "url": f"/combos/{obj.slug}"},
            ]),
        ]
