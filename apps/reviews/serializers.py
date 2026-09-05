# apps/reviews/serializers.py
from rest_framework import serializers
from apps.reviews.models import TourReview, ExternalReview
from apps.core.serializers import cloudinary_image_dict


class TourReviewSerializer(serializers.ModelSerializer):
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model  = TourReview
        fields = [
            "id", "name", "rating", "title", "body",
            "travel_date", "is_verified", "is_featured",
            "admin_response", "created_at",
        ]


class ExternalReviewSerializer(serializers.ModelSerializer):
    reviewer_avatar = serializers.SerializerMethodField()
    tour_title      = serializers.SerializerMethodField()
    tour_slug       = serializers.SerializerMethodField()
    source_label    = serializers.SerializerMethodField()

    class Meta:
        model  = ExternalReview
        fields = [
            "id", "source", "source_label",
            "reviewer_name", "reviewer_location",
            "reviewer_avatar", "rating",
            "title", "body", "review_date",
            "source_url", "is_featured", "order",
            "tour_title", "tour_slug",
        ]

    def get_reviewer_avatar(self, obj) -> dict | None:
        return cloudinary_image_dict(
            obj.reviewer_avatar,
            f"{obj.reviewer_name} review photo"
        )

    def get_tour_title(self, obj) -> str | None:
        return obj.tour.title if obj.tour else None

    def get_tour_slug(self, obj) -> str | None:
        return obj.tour.slug if obj.tour else None

    def get_source_label(self, obj) -> str:
        return obj.get_source_display()
