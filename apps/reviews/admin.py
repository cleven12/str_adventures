# apps/reviews/admin.py

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.admin_mixins import JSONImportMixin
from apps.core.admin_unfold import status_badge
from .models import TourReview, ExternalReview


@admin.register(TourReview)
class TourReviewAdmin(ModelAdmin):
    """⭐ Admin for on-site tour reviews left by past travelers."""
    approved_pill = status_badge('is_approved', description='✅ Approved')
    list_display  = (
        'tour', 'name', 'rating', 'is_verified',
        'approved_pill', 'is_featured', 'created_at'
    )
    list_filter   = ('rating', 'is_approved', 'is_featured', 'tour')
    search_fields = ('name', 'email', 'title', 'body', 'tour__title')
    list_editable = ('is_featured',)
    readonly_fields = ('created_at', 'updated_at', 'is_verified')
    raw_id_fields = ('tour', 'booking', 'user')
    actions = ['approve', 'unapprove', 'feature']

    def approve(self, request, queryset):
        queryset.update(is_approved=True)
    approve.short_description = '✅ Approve selected reviews'

    def unapprove(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove.short_description = '🚫 Unapprove selected reviews'

    def feature(self, request, queryset):
        queryset.update(is_featured=True)
    feature.short_description = '🌟 Mark as featured'


@admin.register(ExternalReview)
class ExternalReviewAdmin(JSONImportMixin, ModelAdmin):
    """🌐 Admin for reviews imported from Google/TripAdvisor/GetYourGuide."""
    list_display  = (
        'reviewer_name', 'source', 'rating',
        'tour', 'review_date', 'is_active', 'is_featured', 'order'
    )
    list_filter   = ('source', 'is_active', 'is_featured', 'rating')
    search_fields = ('reviewer_name', 'title', 'body')
    list_editable = ('is_active', 'is_featured', 'order')
    raw_id_fields = ('tour',)
