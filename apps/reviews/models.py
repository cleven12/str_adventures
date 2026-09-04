# apps/reviews/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

User = get_user_model()


# ============================================================
# TOUR REVIEW — booking-gated, verified
# ============================================================

class TourReview(models.Model):
    tour    = models.ForeignKey(
        'tours.Tour', on_delete=models.CASCADE, related_name='tour_reviews'
    )
    booking = models.OneToOneField(
        'booking.Booking', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='review',
        help_text="Links review to a completed booking — ensures verified status"
    )
    user    = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tour_reviews'
    )

    # ── Review content ────────────────────────────────
    name        = models.CharField(max_length=100)
    email       = models.EmailField(blank=True)
    rating      = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title       = models.CharField(max_length=150, blank=True)
    body        = models.TextField()
    travel_date = models.DateField(
        null=True, blank=True,
        help_text="Month/year of the actual trip"
    )

    # ── Moderation ────────────────────────────────────
    is_approved     = models.BooleanField(default=False)
    is_featured     = models.BooleanField(default=False)
    admin_response  = models.TextField(
        blank=True,
        help_text="Optional public response from VisitKili team"
    )

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'tour_reviews'
        ordering            = ['-created_at']
        verbose_name        = 'Tour Review'
        verbose_name_plural = 'Tour Reviews'
        indexes             = [
            models.Index(fields=['tour', 'is_approved'],   name='review_tour_approved_idx'),
            models.Index(fields=['is_featured'],           name='review_featured_idx'),
        ]

    def __str__(self):
        return f"{self.tour.title} — {self.rating}★ by {self.name}"

    @property
    def is_verified(self):
        return self.booking is not None


# ============================================================
# EXTERNAL REVIEW — manual TripAdvisor imports
# Shows as TripAdvisor-style widget on the site
# ============================================================

class ExternalReview(models.Model):
    SOURCE_CHOICES = [
        ('tripadvisor', 'TripAdvisor'),
        ('google',      'Google'),
        ('facebook',    'Facebook'),
        ('other',       'Other'),
    ]

    tour        = models.ForeignKey(
        'tours.Tour', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='external_reviews',
        help_text="Leave blank for general company reviews"
    )
    source      = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default='tripadvisor'
    )
    reviewer_name   = models.CharField(max_length=100)
    reviewer_location = models.CharField(max_length=100, blank=True)
    reviewer_avatar = CloudinaryField(
        'image', folder='reviews/avatars',
        blank=True, null=True,
        transformation={'width': 80, 'height': 80, 'crop': 'fill', 'fetch_format': 'auto'}
    )
    rating      = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title       = models.CharField(max_length=200, blank=True)
    body        = models.TextField()
    review_date = models.DateField(
        help_text="Date the review was originally posted on the source platform"
    )
    source_url  = models.URLField(
        max_length=500, blank=True,
        help_text="Link to the original review on TripAdvisor/Google"
    )
    is_active   = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order       = models.PositiveIntegerField(default=0)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'external_reviews'
        ordering            = ['order', '-review_date']
        verbose_name        = 'External Review'
        verbose_name_plural = 'External Reviews'
        indexes             = [
            models.Index(fields=['tour', 'is_active'],  name='extreview_tour_idx'),
            models.Index(fields=['source', 'is_active'],name='extreview_source_idx'),
            models.Index(fields=['is_featured'],        name='extreview_featured_idx'),
        ]

    def __str__(self):
        return f"{self.source.title()} — {self.reviewer_name} — {self.rating}★"
