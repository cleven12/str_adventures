# apps/guide/serializers.py
# Guide serializers — TrekGuide + BlogArticle + content blocks.
# Every guide response includes:
#   - primary_tour CTA (the key revenue link in every guide)
#   - related_tours + related_guides + tags (SEO mesh)
#   - content_blocks with anchor IDs (table of contents)
#   - Full Article / HowTo / FAQPage schema.org
#   - GuideInternalLink outgoing_links (rendered as <a> in content)

from django.utils.html import strip_tags
from django.conf import settings
from rest_framework import serializers

from apps.guide.models import (
    GuideCategory, TrekGuide, GuideContentBlock,
    GuideInternalLink, BlogArticle,
)
from apps.core.serializers import (
    SEOFieldsMixin, cloudinary_image_dict, secondary_keywords_list
)
from apps.core.seo_engine import (
    build_guide_schema,
    get_organization_schema,
    get_breadcrumb_schema,
    build_faq_schema,
)

DOMAIN = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
BASE_URL = f"https://{DOMAIN}"


# ── Guide Category ─────────────────────────────────────────────────────────────

class GuideCategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = GuideCategory
        fields = ["id", "name", "slug", "icon"]


class GuideCategorySerializer(serializers.ModelSerializer):
    guide_count   = serializers.SerializerMethodField()
    article_count = serializers.SerializerMethodField()
    url           = serializers.SerializerMethodField()

    class Meta:
        model  = GuideCategory
        fields = [
            "id", "name", "slug", "description", "icon",
            "meta_title", "meta_description",
            "order", "is_active",
            "guide_count", "article_count", "url",
        ]

    def get_guide_count(self, obj) -> int:
        return obj.guides.filter(is_published=True).count()

    def get_article_count(self, obj) -> int:
        return obj.articles.filter(status="published").count()

    def get_url(self, obj) -> str:
        return f"/guides/category/{obj.slug}"


# ── Guide Content Block ────────────────────────────────────────────────────────

class GuideContentBlockSerializer(serializers.ModelSerializer):
    content_plain    = serializers.SerializerMethodField()
    block_type_label = serializers.SerializerMethodField()

    class Meta:
        model  = GuideContentBlock
        fields = [
            "id", "block_type", "block_type_label",
            "heading", "content", "content_plain",
            "anchor_id", "include_in_toc",
            "focus_keyword", "icon", "order",
        ]

    def get_content_plain(self, obj) -> str:
        return strip_tags(str(obj.content)) if obj.content else ""

    def get_block_type_label(self, obj) -> str:
        return obj.get_block_type_display()


# ── Guide Internal Link ────────────────────────────────────────────────────────

class GuideInternalLinkSerializer(serializers.ModelSerializer):
    resolved_url   = serializers.SerializerMethodField()
    link_type_label = serializers.SerializerMethodField()

    class Meta:
        model  = GuideInternalLink
        fields = [
            "id", "anchor_text", "link_type", "link_type_label",
            "is_nofollow", "resolved_url",
        ]

    def get_resolved_url(self, obj) -> str:
        if obj.to_tour:
            return f"/tours/{obj.to_tour.slug}"
        if obj.to_guide:
            return f"/guides/{obj.to_guide.slug}"
        return obj.to_url or "#"

    def get_link_type_label(self, obj) -> str:
        return obj.get_link_type_display()


# ── Trek Guide Card (list view) ────────────────────────────────────────────────

class TrekGuideCardSerializer(serializers.ModelSerializer):
    """
    Lightweight guide card used in:
    - Tour detail related_guides
    - Guide listing page
    - Homepage featured_guides
    - Tag pages
    """
    category       = GuideCategoryMiniSerializer(read_only=True)
    tags           = serializers.SerializerMethodField()
    feature_image  = serializers.SerializerMethodField()
    primary_tour   = serializers.SerializerMethodField()
    url            = serializers.SerializerMethodField()
    author_name    = serializers.SerializerMethodField()

    class Meta:
        model  = TrekGuide
        fields = [
            "id", "title", "slug",
            "category", "tags",
            "excerpt", "first_paragraph",
            "feature_image",
            "difficulty", "reading_time",
            "is_featured", "publish_date",
            "primary_tour",
            "author_name",
            "focus_keyword",
            "url",
        ]

    def get_tags(self, obj) -> list:
        from apps.tours.serializers import TagMiniSerializer
        return TagMiniSerializer(obj.tags.all(), many=True).data

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(
            obj.featured_image,
            obj.image_alt_text or obj.title
        )

    def get_primary_tour(self, obj) -> dict | None:
        if not obj.primary_tour:
            return None
        t = obj.primary_tour
        return {
            "id":    t.id,
            "title": t.title,
            "slug":  t.slug,
            "price_usd": str(t.price_usd),
            "url":   f"/tours/{t.slug}",
        }

    def get_url(self, obj) -> str:
        return f"/guides/{obj.slug}"

    def get_author_name(self, obj) -> str:
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return "Structured Adventures Team"


# ── Trek Guide Detail ──────────────────────────────────────────────────────────

class TrekGuideDetailSerializer(SEOFieldsMixin, serializers.ModelSerializer):
    """
    Full guide response.
    SEO: Article/HowTo/FAQPage schema + BreadcrumbList.
    Mesh: primary_tour CTA + related_tours + related_articles + tags.
    """
    category         = GuideCategorySerializer(read_only=True)
    tags             = serializers.SerializerMethodField()
    content_blocks   = GuideContentBlockSerializer(many=True, read_only=True)
    outgoing_links   = GuideInternalLinkSerializer(many=True, read_only=True)
    primary_tour     = serializers.SerializerMethodField()
    related_tours    = serializers.SerializerMethodField()
    related_articles = serializers.SerializerMethodField()
    table_of_contents = serializers.SerializerMethodField()
    feature_image    = serializers.SerializerMethodField()
    author_name      = serializers.SerializerMethodField()
    url              = serializers.SerializerMethodField()
    nearby_guides    = serializers.SerializerMethodField()

    class Meta:
        model  = TrekGuide
        fields = [
            "id", "title", "slug",
            "category", "tags",
            "first_paragraph", "excerpt", "content",
            "content_blocks", "table_of_contents",
            "outgoing_links",
            "feature_image",
            "difficulty", "reading_time",
            "is_featured", "is_published",
            "publish_date", "updated_at",
            "view_count",
            "author_name",
            "primary_tour", "related_tours", "related_articles",
            "nearby_guides",
            "seo", "url",
        ]

    def get_tags(self, obj) -> list:
        from apps.tours.serializers import TagMiniSerializer
        return TagMiniSerializer(obj.tags.all(), many=True).data

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(
            obj.featured_image, obj.image_alt_text or obj.title
        )

    def get_author_name(self, obj) -> str:
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return "Structured Adventures Team"

    def get_url(self, obj) -> str:
        return f"/guides/{obj.slug}"

    def get_table_of_contents(self, obj) -> list:
        toc = []
        for block in obj.content_blocks.filter(
            include_in_toc=True,
            block_type__in=["heading", "subheading"],
        ).order_by("order"):
            if block.heading and block.anchor_id:
                toc.append({
                    "heading": block.heading,
                    "anchor":  block.anchor_id,
                    "level":   "h2" if block.block_type == "heading" else "h3",
                })
        return toc

    def get_primary_tour(self, obj) -> dict | None:
        if not obj.primary_tour:
            return None
        from apps.tours.serializers import TourCardSerializer
        return TourCardSerializer(
            obj.primary_tour,
            context=self.context,
        ).data

    def get_related_tours(self, obj) -> list:
        from apps.tours.serializers import TourCardSerializer
        qs = (
            obj.related_tours
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags", "gallery")[:4]
        )
        return TourCardSerializer(qs, many=True, context=self.context).data

    def get_related_articles(self, obj) -> list:
        qs = (
            obj.related_articles
            .filter(status="published")
            .select_related("category")[:4]
        )
        return BlogArticleCardSerializer(qs, many=True, context=self.context).data

    def get_nearby_guides(self, obj) -> list:
        """
        Guides in same category + sharing tags — strengthens internal mesh.
        Frontend renders as 'Further Reading' section.
        """
        tag_ids = list(obj.tags.values_list("id", flat=True))
        qs = (
            TrekGuide.objects
            .filter(is_published=True)
            .filter(
                models_Q(category=obj.category) |
                models_Q(tags__in=tag_ids)
            )
            .exclude(pk=obj.pk)
            .distinct()
            .select_related("category")[:4]
        )
        return TrekGuideCardSerializer(qs, many=True, context=self.context).data

    def get_seo_schemas(self, obj) -> list:
        """
        Article / HowTo / FAQPage + Breadcrumb + Organization.
        Uses schema_type field chosen in guide admin.
        """
        schemas = build_guide_schema(obj, request=None)

        # Add BreadcrumbList
        schemas.append(get_breadcrumb_schema([
            {"name": "Home",          "url": "/"},
            {"name": "Travel Guides", "url": "/guides/"},
            {"name": obj.category.name, "url": f"/guides/category/{obj.category.slug}"},
            {"name": obj.title,       "url": f"/guides/{obj.slug}"},
        ]))

        # Add FAQPage if any FAQ content blocks exist
        faq_blocks = obj.content_blocks.filter(block_type="faq").order_by("order")
        if faq_blocks.exists():
            faqs = [
                {"question": b.heading, "answer": strip_tags(str(b.content))}
                for b in faq_blocks
                if b.heading and b.content
            ]
            if faqs:
                schemas.append(build_faq_schema(faqs))

        return schemas


# ── Blog Article Card ──────────────────────────────────────────────────────────

class BlogArticleCardSerializer(serializers.ModelSerializer):
    category       = GuideCategoryMiniSerializer(read_only=True)
    tags           = serializers.SerializerMethodField()
    feature_image  = serializers.SerializerMethodField()
    primary_tour   = serializers.SerializerMethodField()
    url            = serializers.SerializerMethodField()
    author_name    = serializers.SerializerMethodField()

    class Meta:
        model  = BlogArticle
        fields = [
            "id", "title", "slug",
            "category", "tags",
            "excerpt", "first_paragraph",
            "feature_image", "reading_time",
            "status", "published_at",
            "is_featured",
            "primary_tour",
            "author_name",
            "focus_keyword",
            "url",
        ]

    def get_tags(self, obj) -> list:
        from apps.tours.serializers import TagMiniSerializer
        return TagMiniSerializer(obj.tags.all(), many=True).data

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(
            obj.featured_image,
            obj.image_alt_text or obj.title
        )

    def get_primary_tour(self, obj) -> dict | None:
        if not obj.primary_tour:
            return None
        t = obj.primary_tour
        return {"id": t.id, "title": t.title, "slug": t.slug, "url": f"/tours/{t.slug}"}

    def get_url(self, obj) -> str:
        return f"/articles/{obj.slug}"

    def get_author_name(self, obj) -> str:
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return "Structured Adventures Team"


# ── Blog Article Detail ────────────────────────────────────────────────────────

class BlogArticleDetailSerializer(SEOFieldsMixin, serializers.ModelSerializer):
    category       = GuideCategorySerializer(read_only=True)
    tags           = serializers.SerializerMethodField()
    feature_image  = serializers.SerializerMethodField()
    primary_tour   = serializers.SerializerMethodField()
    related_tours  = serializers.SerializerMethodField()
    related_guides = serializers.SerializerMethodField()
    author_name    = serializers.SerializerMethodField()
    url            = serializers.SerializerMethodField()

    class Meta:
        model  = BlogArticle
        fields = [
            "id", "title", "slug",
            "category", "tags",
            "first_paragraph", "excerpt", "content",
            "feature_image", "reading_time",
            "status", "published_at", "updated_at",
            "is_featured",
            "author_name",
            "primary_tour", "related_tours", "related_guides",
            "schema_type",
            "seo", "url",
        ]

    def get_tags(self, obj) -> list:
        from apps.tours.serializers import TagMiniSerializer
        return TagMiniSerializer(obj.tags.all(), many=True).data

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(
            obj.featured_image,
            obj.image_alt_text or obj.title
        )

    def get_author_name(self, obj) -> str:
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return "Structured Adventures Team"

    def get_url(self, obj) -> str:
        return f"/articles/{obj.slug}"

    def get_primary_tour(self, obj) -> dict | None:
        if not obj.primary_tour:
            return None
        from apps.tours.serializers import TourCardSerializer
        return TourCardSerializer(obj.primary_tour, context=self.context).data

    def get_related_tours(self, obj) -> list:
        from apps.tours.serializers import TourCardSerializer
        qs = (
            obj.related_tours
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags", "gallery")[:4]
        )
        return TourCardSerializer(qs, many=True, context=self.context).data

    def get_related_guides(self, obj) -> list:
        qs = (
            obj.related_guides
            .filter(is_published=True)
            .select_related("category")[:4]
        )
        return TrekGuideCardSerializer(qs, many=True, context=self.context).data

    def get_seo_schemas(self, obj) -> list:
        schemas = build_guide_schema(obj, request=None)
        schemas.append(get_breadcrumb_schema([
            {"name": "Home",     "url": "/"},
            {"name": "Articles", "url": "/articles/"},
            {"name": obj.title,  "url": f"/articles/{obj.slug}"},
        ]))
        return schemas


# Avoid circular import — import Q here
try:
    from django.db.models import Q as models_Q
except ImportError:
    from django.db.models import Q as models_Q
