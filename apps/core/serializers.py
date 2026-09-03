# apps/core/serializers.py
# Shared serializers and mixins used across all apps.
# Every serializer that touches SEO builds schema.org automatically.

import json
from django.conf import settings
from django.utils.html import strip_tags
from rest_framework import serializers

from apps.core.models import FAQ, SiteSettings, TeamMember, JobPosting
from apps.core.seo_engine import (
    get_organization_schema,
    get_website_schema,
    get_breadcrumb_schema,
    build_faq_schema,
)

DOMAIN = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
BASE_URL = f"https://{DOMAIN}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def cloudinary_image_dict(field_value, alt_text="") -> dict | None:
    """Convert a CloudinaryField value to a consistent image dict."""
    if not field_value:
        return None
    try:
        url = field_value.url
    except Exception:
        return None
    # Auto format + quality for Next.js Image
    if "cloudinary.com" in url and "f_auto" not in url:
        url = url.replace("/upload/", "/upload/f_auto,q_auto,w_1200/")
    return {"url": url, "alt": alt_text or ""}


def secondary_keywords_list(raw: str) -> list[str]:
    """Parse comma-separated secondary_keywords into a clean list."""
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


# ── Mixins ─────────────────────────────────────────────────────────────────────

class SEOFieldsMixin(serializers.Serializer):
    """
    Mixin: adds `seo` block to any serializer.
    Override `get_seo_schemas()` in child for page-specific schema.org.
    """
    seo = serializers.SerializerMethodField()

    def get_seo(self, obj) -> dict:
        return {
            "meta_title":        getattr(obj, "meta_title", "") or getattr(obj, "title", ""),
            "meta_description":  getattr(obj, "meta_description", "") or getattr(obj, "excerpt", "") or getattr(obj, "short_description", ""),
            "focus_keyword":     getattr(obj, "focus_keyword", ""),
            "secondary_keywords": secondary_keywords_list(getattr(obj, "secondary_keywords", "")),
            "canonical_url":     getattr(obj, "canonical_url", "") or f"{BASE_URL}{obj.get_absolute_url()}",
            "og_title":          getattr(obj, "og_title", "") or getattr(obj, "meta_title", "") or getattr(obj, "title", ""),
            "og_description":    getattr(obj, "og_description", "") or getattr(obj, "meta_description", ""),
            "og_image":          cloudinary_image_dict(getattr(obj, "og_image", None)),
            "twitter_card":      getattr(obj, "twitter_card_type", "summary_large_image"),
            "schema_org":        self.get_seo_schemas(obj),
        }

    def get_seo_schemas(self, obj) -> list:
        """Override in child serializers to return page-specific schemas."""
        return [get_organization_schema()]


# ── Site Settings ──────────────────────────────────────────────────────────────

class SiteSettingsSerializer(serializers.ModelSerializer):
    schema_org = serializers.SerializerMethodField()

    class Meta:
        model  = SiteSettings
        fields = [
            "site_name", "contact_email", "contact_phone",
            "whatsapp_number", "office_address",
            "show_announcement", "announcement_text", "announcement_link",
            "holiday_mode", "holiday_name",
            "default_meta_title", "default_meta_description",
            "schema_org",
        ]

    def get_schema_org(self, obj) -> list:
        return [get_organization_schema(), get_website_schema()]


# ── FAQ ────────────────────────────────────────────────────────────────────────

class FAQSerializer(serializers.ModelSerializer):
    answer_plain = serializers.SerializerMethodField()

    class Meta:
        model  = FAQ
        fields = ["id", "question", "answer", "answer_plain", "order"]

    def get_answer_plain(self, obj) -> str:
        return strip_tags(str(obj.answer))


# ── Team Member ────────────────────────────────────────────────────────────────

class TeamMemberSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model  = TeamMember
        fields = [
            "id", "name", "role", "bio", "photo",
            "linkedin", "years_experience", "summits_count", "order",
        ]

    def get_photo(self, obj) -> dict | None:
        return cloudinary_image_dict(obj.photo, f"{obj.name} — {obj.role}")


# ── Job Posting ────────────────────────────────────────────────────────────────

class JobPostingSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model  = JobPosting
        fields = [
            "id", "title", "slug", "department", "type",
            "location", "description", "requirements",
            "deadline", "created_at", "url",
        ]

    def get_url(self, obj) -> str:
        return f"/careers/{obj.slug}"
