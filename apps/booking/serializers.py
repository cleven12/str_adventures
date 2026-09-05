# apps/booking/serializers.py
# Read-only serializers only — GroupDeparture for display.
# Booking create endpoint is excluded per spec.

from django.utils import timezone
from rest_framework import serializers
from apps.booking.models import GroupDeparture


class GroupDepartureCardSerializer(serializers.ModelSerializer):
    """
    Used in: tour detail, homepage, group listing.
    Includes urgency signals for UI conversion.
    """
    tour            = serializers.SerializerMethodField()
    spots_remaining = serializers.IntegerField(read_only=True)
    fill_percentage = serializers.IntegerField(read_only=True)
    urgency_label   = serializers.CharField(read_only=True)
    has_reached_minimum = serializers.BooleanField(read_only=True)
    days_until_departure = serializers.SerializerMethodField()
    is_accepting_requests = serializers.BooleanField(read_only=True)
    status_label    = serializers.SerializerMethodField()
    feature_badge_label = serializers.SerializerMethodField()
    url             = serializers.SerializerMethodField()

    class Meta:
        model  = GroupDeparture
        fields = [
            "id", "title", "slug",
            "tour",
            "start_date", "end_date",
            "price_per_person",
            "capacity", "current_count",
            "spots_remaining", "fill_percentage",
            "status", "status_label",
            "feature_badge", "feature_badge_label",
            "urgency_label", "has_reached_minimum",
            "is_accepting_requests",
            "days_until_departure",
            "benefits_text", "description",
            "show_on_homepage",
            "url",
        ]

    def get_tour(self, obj) -> dict:
        t = obj.tour
        return {
            "id":         t.id,
            "title":      t.title,
            "slug":       t.slug,
            "difficulty": t.difficulty,
            "difficulty_label": t.get_difficulty_display(),
            "duration_days": t.duration_days,
            "feature_image": self._tour_image(t),
            "url":        f"/tours/{t.slug}",
        }

    def _tour_image(self, tour) -> dict | None:
        from apps.core.serializers import cloudinary_image_dict
        return cloudinary_image_dict(tour.feature_image, tour.title)

    def get_days_until_departure(self, obj) -> int:
        delta = obj.start_date - timezone.now()
        return max(0, delta.days)

    def get_status_label(self, obj) -> str:
        return obj.get_status_display()

    def get_feature_badge_label(self, obj) -> str:
        return obj.get_feature_badge_display() if obj.feature_badge else ""

    def get_url(self, obj) -> str:
        return f"/groups/{obj.slug}"
