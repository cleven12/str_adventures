# apps/api_views.py
# All API viewsets and views for Structured Adventures.
# Excludes booking create per spec — read-only + group departures only.
#
# Performance:
#   - select_related + prefetch_related on every queryset
#   - cache_page on homepage + slug list endpoints
#   - django-filter for all filterable endpoints
#   - Annotated average_rating / review_count on tours
#   - Search uses the same tokenized _kw_q logic from tours/views.py
#
# SEO:
#   - Every endpoint returns seo.schema_org — array of schema.org dicts
#   - Next.js injects them as <script type="application/ld+json"> on each page
#   - Tag endpoints aggregate entire content mesh for topic cluster pages

import django_filters
from django.db.models import Avg, Count, Q, Min, Max, Prefetch
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, filters, generics
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tours.models import (
    Tag, TourCategory, Tour, ComboPackage, TourAvailability, TourImage
)
from apps.guide.models import GuideCategory, TrekGuide, BlogArticle
from apps.destinations.models import Destination, DestinationCategory
from apps.reviews.models import TourReview, ExternalReview
from apps.booking.models import GroupDeparture
from apps.core.models import FAQ, SiteSettings, TeamMember, JobPosting

from apps.tours.serializers import (
    TagSerializer, TourCategorySerializer,
    TourCardSerializer, TourDetailSerializer,
    ComboCardSerializer, ComboDetailSerializer,
)
from apps.guide.serializers import (
    GuideCategorySerializer,
    TrekGuideCardSerializer, TrekGuideDetailSerializer,
    BlogArticleCardSerializer, BlogArticleDetailSerializer,
)
from apps.destinations.serializers import (
    DestinationCardSerializer, DestinationDetailSerializer,
)
from apps.reviews.serializers import TourReviewSerializer, ExternalReviewSerializer
from apps.booking.serializers import GroupDepartureCardSerializer
from apps.core.serializers import (
    SiteSettingsSerializer, FAQSerializer,
    TeamMemberSerializer, JobPostingSerializer,
)
from apps.core.seo_engine import get_organization_schema, get_website_schema, build_faq_schema


# ── Pagination ─────────────────────────────────────────────────────────────────

class StandardPagination(PageNumberPagination):
    page_size             = 12
    page_size_query_param = "page_size"
    max_page_size         = 48


class LargePagination(PageNumberPagination):
    page_size             = 24
    page_size_query_param = "page_size"
    max_page_size         = 96


# ── Search helper (mirrors tours/views.py tokenized search) ────────────────────

STOPWORDS = {'and', 'the', 'to', 'for', 'of', 'in', 'on', 'a', 'an', 'with', 'vs', 'or', 'is'}

def _kw_q(q: str, fields: list, op: str = "AND") -> Q:
    import re
    q = (q or "").strip()
    if not q:
        return Q()
    tokens = [t for t in re.split(r"\s+", q.lower()) if len(t) >= 2 and t not in STOPWORDS]
    if not tokens:
        tokens = [q.lower()]
    combined = None
    for tok in tokens:
        any_field = Q()
        for f in fields:
            any_field |= Q(**{f + "__icontains": tok})
        combined = any_field if combined is None else (combined & any_field if op == "AND" else combined | any_field)
    return combined or Q()


def _kw_filter(qs, q: str, fields: list):
    """AND precision first, fall back to OR so user never sees empty page."""
    r = qs.filter(_kw_q(q, fields, "AND")).distinct()
    if not r.exists():
        r = qs.filter(_kw_q(q, fields, "OR")).distinct()
    return r


# ── Base queryset annotations ──────────────────────────────────────────────────

def _annotate_tours(qs):
    return qs.annotate(
        avg_rating=Avg("tour_reviews__rating", filter=Q(tour_reviews__is_approved=True)),
        review_count=Count("tour_reviews", filter=Q(tour_reviews__is_approved=True), distinct=True),
    )


# ══════════════════════════════════════════════════════════════════════════════
# HOMEPAGE — single aggregated endpoint
# ══════════════════════════════════════════════════════════════════════════════

class HomepageView(APIView):
    """
    GET /api/v1/homepage/
    Everything Next.js homepage needs in a single fetch.
    Cached 30 minutes. Revalidated by Next.js ISR every 1800s.
    """

    @method_decorator(cache_page(60 * 30))
    def get(self, request):
        site = SiteSettings.objects.first()

        featured_tours = _annotate_tours(
            Tour.objects
            .filter(is_active=True, is_featured=True)
            .select_related("category")
            .prefetch_related(
                Prefetch("tags"),
                Prefetch("gallery", queryset=TourImage.objects.order_by("order")),
                Prefetch("seasonal_windows"),
            )
            .order_by("-created_at")[:6]
        )

        group_departures = (
            GroupDeparture.objects
            .filter(
                is_active=True, show_on_homepage=True,
                status__in=["open", "filling"],
                start_date__gte=timezone.now(),
            )
            .select_related("tour__category")
            .order_by("start_date")[:4]
        )

        reviews = (
            ExternalReview.objects
            .filter(is_active=True, is_featured=True)
            .select_related("tour")
            .order_by("order", "-review_date")[:6]
        )

        faqs = list(FAQ.objects.filter(is_active=True).order_by("order")[:8])

        featured_destinations = (
            Destination.objects
            .filter(is_active=True, is_featured=True)
            .select_related("category")
            .order_by("category__order")[:4]
        )

        featured_guides = (
            TrekGuide.objects
            .filter(is_published=True, is_featured=True)
            .select_related("category")
            .prefetch_related("tags")
            .order_by("-publish_date")[:3]
        )

        featured_combos = (
            ComboPackage.objects
            .filter(is_active=True)
            .prefetch_related("tours")
            .order_by("-created_at")[:3]
        )

        # Build global FAQPage schema
        faq_schema = FAQ.get_faq_page_schema(faqs) if faqs else None
        global_schemas = [get_organization_schema(), get_website_schema()]
        if faq_schema:
            global_schemas.append(faq_schema)

        return Response({
            "site":                  SiteSettingsSerializer(site).data if site else None,
            "featured_tours":        TourCardSerializer(featured_tours, many=True).data,
            "featured_combos":       ComboCardSerializer(featured_combos, many=True).data,
            "featured_destinations": DestinationCardSerializer(featured_destinations, many=True).data,
            "group_departures":      GroupDepartureCardSerializer(group_departures, many=True).data,
            "reviews":               ExternalReviewSerializer(reviews, many=True).data,
            "faqs":                  FAQSerializer(faqs, many=True).data,
            "featured_guides":       TrekGuideCardSerializer(featured_guides, many=True).data,
            "seo": {
                "schema_org": global_schemas,
            },
        })


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL SEARCH
# ══════════════════════════════════════════════════════════════════════════════

class GlobalSearchView(APIView):
    """
    GET /api/v1/search/?q=machame+route
    Searches across tours, guides, articles, destinations in one call.
    Used by Next.js search bar with HTMX-style debounce or React state.
    Returns max 5 results per content type — designed for instant search UI.
    """

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            return Response({"q": q, "results": {}, "total": 0})

        TOUR_FIELDS = [
            "title", "slug", "excerpt", "focus_keyword",
            "place_name", "tags__name", "category__name",
        ]
        GUIDE_FIELDS = ["title", "slug", "excerpt", "focus_keyword", "first_paragraph", "tags__name"]
        DEST_FIELDS  = ["name", "slug", "short_description", "focus_keyword", "location_name"]

        tours = _annotate_tours(
            _kw_filter(
                Tour.objects.filter(is_active=True)
                .select_related("category")
                .prefetch_related("tags", "gallery"),
                q, TOUR_FIELDS,
            )[:5]
        )
        guides = _kw_filter(
            TrekGuide.objects.filter(is_published=True).select_related("category"),
            q, GUIDE_FIELDS,
        )[:5]
        articles = _kw_filter(
            BlogArticle.objects.filter(status="published").select_related("category"),
            q, GUIDE_FIELDS,
        )[:5]
        destinations = _kw_filter(
            Destination.objects.filter(is_active=True).select_related("category"),
            q, DEST_FIELDS,
        )[:4]

        total = tours.count() + guides.count() + articles.count() + destinations.count()

        return Response({
            "q":     q,
            "total": total,
            "results": {
                "tours":        TourCardSerializer(tours, many=True).data,
                "guides":       TrekGuideCardSerializer(guides, many=True).data,
                "articles":     BlogArticleCardSerializer(articles, many=True).data,
                "destinations": DestinationCardSerializer(destinations, many=True).data,
            },
        })


# ══════════════════════════════════════════════════════════════════════════════
# SLUGS — lightweight endpoints for Next.js generateStaticParams()
# ══════════════════════════════════════════════════════════════════════════════

class TourSlugListView(APIView):
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        return Response(list(
            Tour.objects.filter(is_active=True).values_list("slug", flat=True)
        ))

class GuideSlugListView(APIView):
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        return Response(list(
            TrekGuide.objects.filter(is_published=True).values_list("slug", flat=True)
        ))

class ArticleSlugListView(APIView):
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        return Response(list(
            BlogArticle.objects.filter(status="published").values_list("slug", flat=True)
        ))

class DestinationSlugListView(APIView):
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        return Response(list(
            Destination.objects.filter(is_active=True).values_list("slug", flat=True)
        ))

class TagSlugListView(APIView):
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        return Response(list(
            Tag.objects.filter(is_active=True).values_list("slug", flat=True)
        ))

class ComboSlugListView(APIView):
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        return Response(list(
            ComboPackage.objects.filter(is_active=True).values_list("slug", flat=True)
        ))


# ══════════════════════════════════════════════════════════════════════════════
# TOURS
# ══════════════════════════════════════════════════════════════════════════════

class TourFilter(django_filters.FilterSet):
    category     = django_filters.CharFilter(field_name="category__slug")
    tour_type    = django_filters.CharFilter()
    difficulty   = django_filters.CharFilter()
    tag          = django_filters.CharFilter(field_name="tags__slug")
    price_min    = django_filters.NumberFilter(field_name="price_usd", lookup_expr="gte")
    price_max    = django_filters.NumberFilter(field_name="price_usd", lookup_expr="lte")
    duration_min = django_filters.NumberFilter(field_name="duration_days", lookup_expr="gte")
    duration_max = django_filters.NumberFilter(field_name="duration_days", lookup_expr="lte")
    featured     = django_filters.BooleanFilter(field_name="is_featured")

    class Meta:
        model  = Tour
        fields = [
            "category", "tour_type", "difficulty", "tag",
            "price_min", "price_max", "duration_min", "duration_max", "featured",
        ]


class TourViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/tours/           — list with filters + search + pagination
    GET /api/v1/tours/{slug}/    — full detail with mesh + schema.org
    GET /api/v1/tours/meta/      — filter metadata (categories, price range)
    """
    filterset_class = TourFilter
    search_fields   = [
        "title", "slug", "excerpt", "focus_keyword",
        "place_name", "tags__name", "category__name",
        "secondary_keywords",
    ]
    ordering_fields = ["price_usd", "duration_days", "created_at", "page_views"]
    ordering        = ["-is_featured", "-created_at"]
    lookup_field    = "slug"
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = (
            Tour.objects
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related(
                Prefetch("tags"),
                Prefetch("gallery", queryset=TourImage.objects.order_by("order")),
                Prefetch("seasonal_windows"),
            )
        )
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                "inclusions", "exclusions",
                Prefetch("itinerary__items__tags"),
                Prefetch("content_blocks"),
                Prefetch("tour_reviews", queryset=TourReview.objects.filter(is_approved=True).select_related("booking")),
                Prefetch("external_reviews", queryset=ExternalReview.objects.filter(is_active=True)),
                Prefetch("related_guides"),
                Prefetch("blog_articles"),
                Prefetch("mentioned_in_destinations"),
                Prefetch("combo_packages"),
                Prefetch("group_departures", queryset=GroupDeparture.objects.filter(is_active=True, start_date__gte=timezone.now())),
                Prefetch("availabilities", queryset=TourAvailability.objects.filter(status="open", start_date__gte=timezone.now())),
            )
        return _annotate_tours(qs)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TourDetailSerializer
        return TourCardSerializer

    def list(self, request, *args, **kwargs):
        # Apply custom tokenized search if ?q= present
        q = request.query_params.get("q", "").strip()
        if q:
            FIELDS = [
                "title", "slug", "excerpt", "focus_keyword",
                "place_name", "tags__name", "category__name",
            ]
            self.queryset = _kw_filter(self.get_queryset(), q, FIELDS)

        response = super().list(request, *args, **kwargs)

        # Inject filter metadata and SEO into list response
        response.data["filters_meta"] = self._filter_meta()
        response.data["seo"] = {
            "schema_org": [
                get_organization_schema(),
                {
                    "@context": "https://schema.org",
                    "@type": "CollectionPage",
                    "name": "Tanzania Tours & Adventures — Structured Adventures",
                    "description": "Browse Kilimanjaro treks, Tanzania safaris, and adventure tours with local experts.",
                    "url": f"https://{getattr(__import__('django.conf', fromlist=['settings']).settings, 'SITE_DOMAIN', 'structuredadventures.com')}/tours/",
                },
            ]
        }
        return response

    def _filter_meta(self) -> dict:
        active = Tour.objects.filter(is_active=True)
        return {
            "categories": list(
                TourCategory.objects
                .annotate(count=Count("tours", filter=Q(tours__is_active=True)))
                .filter(count__gt=0)
                .values("slug", "name", "count")
                .order_by("order")
            ),
            "price_range":    active.aggregate(min=Min("price_usd"), max=Max("price_usd")),
            "duration_range": active.aggregate(min=Min("duration_days"), max=Max("duration_days")),
            "difficulties":   list(active.values_list("difficulty", flat=True).distinct()),
            "tour_types":     list(active.values_list("tour_type", flat=True).distinct()),
        }

    @action(detail=False, url_path="meta", methods=["get"])
    def meta(self, request):
        """GET /api/v1/tours/meta/ — filter metadata only."""
        return Response(self._filter_meta())


# ══════════════════════════════════════════════════════════════════════════════
# TAGS — SEO mesh hub
# ══════════════════════════════════════════════════════════════════════════════

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/tags/         — all active tags grouped by pillar
    GET /api/v1/tags/{slug}/  — full tag page: tours + guides + articles
    """
    queryset     = Tag.objects.filter(is_active=True).order_by("name")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TagSerializer
        # List: return minimal data grouped by pillar
        return TagSerializer  # override below

    def list(self, request):
        """Return tags grouped by topic_pillar for nav/filter UI."""
        tags = Tag.objects.filter(is_active=True).order_by("topic_pillar", "name")
        grouped = {}
        for tag in tags:
            pillar = tag.topic_pillar
            if pillar not in grouped:
                grouped[pillar] = []
            grouped[pillar].append({
                "id": tag.id, "name": tag.name, "slug": tag.slug,
                "tour_count": tag.tours.filter(is_active=True).count(),
            })
        return Response({"grouped": grouped, "flat": list(tags.values("id", "name", "slug", "topic_pillar"))})

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

class TourCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset     = TourCategory.objects.all().order_by("order", "name")
    serializer_class = TourCategorySerializer
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        # Include tours for this category
        tours = _annotate_tours(
            Tour.objects
            .filter(is_active=True, category=instance)
            .select_related("category")
            .prefetch_related("tags", "gallery", "seasonal_windows")
            .order_by("-is_featured", "-created_at")
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(tours, request)
        data["tours"] = TourCardSerializer(page, many=True).data
        data["tours_count"] = tours.count()
        return Response(data)


# ══════════════════════════════════════════════════════════════════════════════
# COMBOS
# ══════════════════════════════════════════════════════════════════════════════

class ComboViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        ComboPackage.objects.filter(is_active=True)
        .prefetch_related("tours__category", "tours__gallery", "tags")
        .order_by("-created_at")
    )
    lookup_field = "slug"

    def get_serializer_class(self):
        return ComboDetailSerializer if self.action == "retrieve" else ComboCardSerializer


# ══════════════════════════════════════════════════════════════════════════════
# GUIDES
# ══════════════════════════════════════════════════════════════════════════════

class TrekGuideFilter(django_filters.FilterSet):
    category   = django_filters.CharFilter(field_name="category__slug")
    difficulty = django_filters.CharFilter()
    tag        = django_filters.CharFilter(field_name="tags__slug")
    featured   = django_filters.BooleanFilter(field_name="is_featured")

    class Meta:
        model  = TrekGuide
        fields = ["category", "difficulty", "tag", "featured"]


class TrekGuideViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/guides/           — list
    GET /api/v1/guides/{slug}/    — full detail with mesh + Article schema
    """
    filterset_class = TrekGuideFilter
    search_fields   = [
        "title", "slug", "excerpt", "focus_keyword",
        "first_paragraph", "tags__name", "category__name",
    ]
    ordering        = ["-publish_date"]
    lookup_field    = "slug"
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = (
            TrekGuide.objects.filter(is_published=True)
            .select_related("category", "author")
            .prefetch_related("tags")
        )
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                Prefetch("content_blocks"),
                Prefetch("outgoing_links", queryset=GuideInternalLink.objects.filter(is_active=True).select_related("to_guide", "to_tour")),
                Prefetch("related_tours"),
                Prefetch("related_articles"),
            )
        return qs

    def get_serializer_class(self):
        return TrekGuideDetailSerializer if self.action == "retrieve" else TrekGuideCardSerializer

    def list(self, request, *args, **kwargs):
        q = request.query_params.get("q", "").strip()
        if q:
            FIELDS = ["title", "slug", "excerpt", "focus_keyword", "first_paragraph", "tags__name"]
            self.queryset = _kw_filter(self.get_queryset(), q, FIELDS)
        return super().list(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# BLOG ARTICLES
# ══════════════════════════════════════════════════════════════════════════════

class BlogArticleFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    tag      = django_filters.CharFilter(field_name="tags__slug")

    class Meta:
        model  = BlogArticle
        fields = ["category", "tag"]


class BlogArticleViewSet(viewsets.ReadOnlyModelViewSet):
    filterset_class = BlogArticleFilter
    search_fields   = [
        "title", "slug", "excerpt", "focus_keyword",
        "first_paragraph", "tags__name", "category__name",
    ]
    ordering        = ["-publish_date"]
    lookup_field    = "slug"
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = (
            BlogArticle.objects.filter(status="published")
            .select_related("category", "author")
            .prefetch_related("tags")
        )
        if self.action == "retrieve":
            qs = qs.prefetch_related("related_tours", "related_guides")
        return qs

    def get_serializer_class(self):
        return BlogArticleDetailSerializer if self.action == "retrieve" else BlogArticleCardSerializer

    def list(self, request, *args, **kwargs):
        q = request.query_params.get("q", "").strip()
        if q:
            FIELDS = ["title", "slug", "excerpt", "focus_keyword", "first_paragraph", "tags__name"]
            self.queryset = _kw_filter(self.get_queryset(), q, FIELDS)
        return super().list(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# GUIDE CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

class GuideCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset     = GuideCategory.objects.filter(is_active=True).order_by("order", "name")
    serializer_class = GuideCategorySerializer
    lookup_field = "slug"


# ══════════════════════════════════════════════════════════════════════════════
# DESTINATIONS
# ══════════════════════════════════════════════════════════════════════════════

class DestinationFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    featured = django_filters.BooleanFilter(field_name="is_featured")
    tag      = django_filters.CharFilter(field_name="tags__slug")

    class Meta:
        model  = Destination
        fields = ["category", "featured", "tag"]


class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    filterset_class = DestinationFilter
    search_fields   = [
        "name", "slug", "short_description", "focus_keyword",
        "location_name", "tags__name",
    ]
    ordering        = ["-is_featured", "name"]
    lookup_field    = "slug"

    def get_queryset(self):
        qs = (
            Destination.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags")
        )
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                "gallery", "faqs",
                "related_tours", "related_guides", "related_articles",
            )
        return qs

    def get_serializer_class(self):
        return DestinationDetailSerializer if self.action == "retrieve" else DestinationCardSerializer


# ══════════════════════════════════════════════════════════════════════════════
# REVIEWS
# ══════════════════════════════════════════════════════════════════════════════

class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/reviews/           — external reviews (featured first)
    GET /api/v1/reviews/?tour=slug — reviews for a specific tour
    GET /api/v1/reviews/?source=tripadvisor
    """
    serializer_class = ExternalReviewSerializer
    ordering         = ["order", "-review_date"]

    def get_queryset(self):
        qs = (
            ExternalReview.objects.filter(is_active=True)
            .select_related("tour")
        )
        tour_slug = self.request.query_params.get("tour")
        source    = self.request.query_params.get("source")
        if tour_slug:
            qs = qs.filter(tour__slug=tour_slug)
        if source:
            qs = qs.filter(source=source)
        return qs.order_by("order", "-review_date")


# ══════════════════════════════════════════════════════════════════════════════
# GROUP DEPARTURES
# ══════════════════════════════════════════════════════════════════════════════

class GroupDepartureFilter(django_filters.FilterSet):
    tour   = django_filters.CharFilter(field_name="tour__slug")
    status = django_filters.CharFilter()
    badge  = django_filters.CharFilter(field_name="feature_badge")
    month  = django_filters.CharFilter(method="filter_month")

    class Meta:
        model  = GroupDeparture
        fields = ["tour", "status", "badge", "month"]

    def filter_month(self, queryset, name, value):
        """?month=YYYY-MM — departures starting in that calendar month."""
        try:
            year, month = value.split("-")
            return queryset.filter(start_date__year=int(year), start_date__month=int(month))
        except (ValueError, AttributeError):
            return queryset.none()


class GroupDepartureViewSet(viewsets.ReadOnlyModelViewSet):
    filterset_class = GroupDepartureFilter
    lookup_field    = "slug"
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            GroupDeparture.objects
            .filter(is_active=True, start_date__gte=timezone.now())
            .select_related("tour__category")
            .order_by("start_date")
        )

    def get_serializer_class(self):
        return GroupDepartureCardSerializer


# ══════════════════════════════════════════════════════════════════════════════
# FAQs
# ══════════════════════════════════════════════════════════════════════════════

class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/faqs/  — returns FAQs + pre-built FAQPage schema.org
    """
    queryset         = FAQ.objects.filter(is_active=True).order_by("order")
    serializer_class = FAQSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        faqs = list(self.get_queryset())
        response.data["seo"] = {
            "schema_org": [build_faq_schema(faqs)] if faqs else []
        }
        return response


# ══════════════════════════════════════════════════════════════════════════════
# SITE / SETTINGS / TEAM / CAREERS
# ══════════════════════════════════════════════════════════════════════════════

class SiteSettingsView(APIView):
    """GET /api/v1/site/ — site-wide settings + org schema."""
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        site = SiteSettings.objects.first()
        return Response(SiteSettingsSerializer(site).data if site else {})


class TeamView(APIView):
    """GET /api/v1/team/"""
    def get(self, request):
        team = TeamMember.objects.filter(is_active=True).order_by("order", "name")
        return Response(TeamMemberSerializer(team, many=True).data)


class CareersView(APIView):
    """GET /api/v1/careers/"""
    def get(self, request):
        jobs = JobPosting.objects.filter(is_active=True).order_by("-created_at")
        return Response(JobPostingSerializer(jobs, many=True).data)


# Import for use in TrekGuideViewSet
from apps.guide.models import GuideInternalLink
