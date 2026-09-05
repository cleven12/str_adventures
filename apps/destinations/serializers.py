# apps/destinations/serializers.py
from django.conf import settings
from rest_framework import serializers

from apps.destinations.models import Destination, DestinationCategory, DestinationGallery, DestinationFAQ
from apps.core.serializers import SEOFieldsMixin, cloudinary_image_dict
from apps.core.seo_engine import build_destination_schema, get_organization_schema, get_breadcrumb_schema

DOMAIN = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
BASE_URL = f"https://{DOMAIN}"


class DestinationCategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DestinationCategory
        fields = ["id", "name", "slug"]


class DestinationFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DestinationFAQ
        fields = ["id", "question", "answer", "order"]


class DestinationGallerySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model  = DestinationGallery
        fields = ["id", "url", "alt_text", "order"]

    def get_url(self, obj) -> str | None:
        try:
            return obj.image.url
        except Exception:
            return None


class DestinationCardSerializer(serializers.ModelSerializer):
    category      = DestinationCategoryMiniSerializer(read_only=True)
    feature_image = serializers.SerializerMethodField()
    url           = serializers.SerializerMethodField()

    class Meta:
        model  = Destination
        fields = [
            "id", "name", "slug",
            "category", "short_description",
            "feature_image", "is_featured",
            "altitude", "best_time_to_visit",
            "focus_keyword", "url",
        ]

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(obj.feature_image, obj.name)

    def get_url(self, obj) -> str:
        return f"/destinations/{obj.slug}"


class DestinationDetailSerializer(SEOFieldsMixin, serializers.ModelSerializer):
    category       = DestinationCategoryMiniSerializer(read_only=True)
    gallery        = DestinationGallerySerializer(many=True, read_only=True)
    faqs           = DestinationFAQSerializer(many=True, read_only=True)
    feature_image  = serializers.SerializerMethodField()
    related_tours  = serializers.SerializerMethodField()
    related_guides = serializers.SerializerMethodField()
    related_articles = serializers.SerializerMethodField()
    tags           = serializers.SerializerMethodField()
    url            = serializers.SerializerMethodField()

    class Meta:
        model  = Destination
        fields = [
            "id", "name", "slug",
            "category", "tags",
            "short_description", "description",
            "feature_image", "gallery",
            "location_name", "altitude", "best_time_to_visit",
            "faqs",
            "related_tours", "related_guides", "related_articles",
            "is_featured", "is_active",
            "seo", "url",
        ]

    def get_feature_image(self, obj) -> dict | None:
        return cloudinary_image_dict(obj.feature_image, obj.name)

    def get_url(self, obj) -> str:
        return f"/destinations/{obj.slug}"

    def get_tags(self, obj) -> list:
        from apps.tours.serializers import TagMiniSerializer
        return TagMiniSerializer(obj.tags.all(), many=True).data

    def get_related_tours(self, obj) -> list:
        from apps.tours.serializers import TourCardSerializer
        qs = (
            obj.related_tours
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related("tags", "gallery")[:6]
        )
        return TourCardSerializer(qs, many=True, context=self.context).data

    def get_related_guides(self, obj) -> list:
        from apps.guide.serializers import TrekGuideCardSerializer
        qs = (
            obj.related_guides
            .filter(is_published=True)
            .select_related("category")[:4]
        )
        return TrekGuideCardSerializer(qs, many=True, context=self.context).data

    def get_related_articles(self, obj) -> list:
        from apps.guide.serializers import BlogArticleCardSerializer
        qs = (
            obj.related_articles
            .filter(status="published")
            .select_related("category")[:4]
        )
        return BlogArticleCardSerializer(qs, many=True, context=self.context).data

    def get_seo_schemas(self, obj) -> list:
        schemas = build_destination_schema(obj, request=None)
        schemas.append(get_breadcrumb_schema([
            {"name": "Home",         "url": "/"},
            {"name": "Destinations", "url": "/destinations/"},
            {"name": obj.name,       "url": f"/destinations/{obj.slug}"},
        ]))
        return schemas
