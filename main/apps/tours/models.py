# apps/tours/models.py
# Product marketing only — Tour, Category, Tag, Images, SEO, Content, Itinerary, Guide content
# Booking, Payment, Reviews live in their own apps

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django_ckeditor_5.fields import CKEditor5Field
from cloudinary.models import CloudinaryField
from apps.core.validators import (
    validate_image_size,
    validate_image_format,
    get_image_upload_help_text,
)

User = get_user_model()


# ============================================================
# TAG — foundation of the entire SEO mesh network
# M2M to Tour, ItineraryItem (guide app handles its own tags)
# ============================================================

class Tag(models.Model):
    TOPIC_PILLAR_CHOICES = [
        ('route',         'Kilimanjaro Route'),
        ('destination',   'Destination / Park'),
        ('activity',      'Activity Type'),
        ('difficulty',    'Difficulty Level'),
        ('season',        'Season / Timing'),
        ('wildlife',      'Wildlife'),
        ('accommodation', 'Accommodation'),
        ('general',       'General'),
    ]

    name            = models.CharField(max_length=120, unique=True)
    slug            = models.SlugField(unique=True, blank=True)
    description     = models.TextField(
        blank=True,
        help_text="SEO copy shown on the tag landing page (/tours/tag/slug/)"
    )
    meta_title      = models.CharField(max_length=60, blank=True)
    meta_description= models.CharField(max_length=155, blank=True)
    topic_pillar    = models.CharField(
        max_length=20,
        choices=TOPIC_PILLAR_CHOICES,
        default='general',
    )
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug'],         name='tag_slug_idx'),
            models.Index(fields=['topic_pillar'], name='tag_pillar_idx'),
            models.Index(fields=['is_active'],    name='tag_active_idx'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Tag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tours:tag_page', kwargs={'slug': self.slug})

    @property
    def seo_score(self):
        score = 30
        if self.focus_keyword or self.name:
            score += 25
        if self.meta_title:
            score += 15
        if self.meta_description:
            score += 15
        if self.description:
            score += 15
        return min(100, score)


# ============================================================
# TOUR CATEGORY
# ============================================================

class TourCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    meta_title  = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=155, blank=True)
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table           = 'tour_category'
        verbose_name_plural= 'Tour Categories'
        ordering           = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tours:category_page', kwargs={'slug': self.slug})


# ============================================================
# INCLUSION / EXCLUSION
# ============================================================

class Inclusion(models.Model):
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon        = models.CharField(
        max_length=50, blank=True,
        help_text="Lucide icon name e.g. 'utensils', 'shield', 'user'"
    )

    class Meta:
        db_table           = 'inclusions'
        verbose_name_plural= 'Inclusions'
        ordering           = ['name']

    def __str__(self):
        return self.name


class Exclusion(models.Model):
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        db_table           = 'exclusions'
        verbose_name_plural= 'Exclusions'
        ordering           = ['name']

    def __str__(self):
        return self.name


# ============================================================
# ITINERARY + ITEMS
# ============================================================

class Itinerary(models.Model):
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'tour_itinerary'
        ordering  = ['name']
        verbose_name_plural = 'Itineraries'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ItineraryItem(models.Model):
    itinerary  = models.ForeignKey(
        Itinerary, on_delete=models.CASCADE, related_name='items'
    )
    day_number = models.PositiveIntegerField(
        help_text="Day number (1,2,3…) or 0 for time-based day trips"
    )
    time       = models.CharField(
        max_length=50, blank=True,
        help_text="e.g. '08:00 AM' — for day trips only"
    )
    title       = models.CharField(max_length=200)
    description = models.TextField()
    tags        = models.ManyToManyField(
        Tag, blank=True, related_name='itinerary_items'
    )
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table       = 'itinerary_items'
        ordering       = ['order', 'day_number', 'time']
        unique_together= [['itinerary', 'day_number', 'time']]
        verbose_name        = 'Itinerary Item'
        verbose_name_plural = 'Itinerary Items'

    def __str__(self):
        return f"{self.itinerary.name} — Day {self.day_number}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = self.day_number or 1
        super().save(*args, **kwargs)


# ============================================================
# TOUR
# ============================================================

class Tour(models.Model):

    DIFFICULTY_CHOICES = [
        ('easy',        'Easy'),
        ('moderate',    'Moderate'),
        ('challenging', 'Challenging'),
        ('extreme',     'Extreme'),
    ]

    TOUR_TYPE_CHOICES = [
        ('multi_day_trek', 'Multi-Day Trek'),
        ('day_trip',       'Day Trip'),
        ('safari',         'Safari'),
        ('beach',          'Beach'),
        ('combo',          'Combo Package'),
    ]

    LODGE_LEVEL_CHOICES = [
        ('basic',      'Basic / Camping'),
        ('mid_range',  'Mid-Range Lodge'),
        ('luxury',     'Luxury'),
        ('ultra_lux',  'Ultra-Luxury / Signature'),
    ]

    BEACH_TYPE_CHOICES = [
        ('relax',      'Relaxation'),
        ('adventure',  'Water Sports / Adventure'),
        ('honeymoon',  'Honeymoon / Romantic'),
    ]

    SCHEMA_TYPE_CHOICES = [
        ('TouristTrip', 'Tourist Trip'),
        ('Product',     'Product'),
        ('Event',       'Event'),
    ]

    # ── Core ─────────────────────────────────────────
    title       = models.CharField(
        max_length=200,
        help_text="Keep under 60 chars for best SERP display."
    )
    slug        = models.SlugField(unique=True, blank=True)
    category    = models.ForeignKey(
        TourCategory, on_delete=models.CASCADE, related_name='tours'
    )
    tags        = models.ManyToManyField(
        Tag, blank=True, related_name='tours'
    )
    tour_type   = models.CharField(
        max_length=20, choices=TOUR_TYPE_CHOICES, default='multi_day_trek'
    )
    place_name  = models.CharField(
        max_length=200,
        help_text="e.g. Mount Kilimanjaro, Serengeti National Park"
    )

    # ── Description / content ────────────────────────
    description = CKEditor5Field(
        config_name='extends',
        help_text="Full tour description — used as fallback if no content blocks exist."
    )
    excerpt     = models.TextField(
        max_length=300, blank=True,
        help_text="150–300 chars. Used in cards and meta description fallback."
    )

    # ── Itinerary ────────────────────────────────────
    itinerary   = models.ForeignKey(
        Itinerary, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tours'
    )

    # ── Inclusions / Exclusions ───────────────────────
    inclusions  = models.ManyToManyField(Inclusion, blank=True, related_name='tours')
    exclusions  = models.ManyToManyField(Exclusion, blank=True, related_name='tours')

    # ── Pricing ───────────────────────────────────────
    price_usd        = models.DecimalField(max_digits=8, decimal_places=2)
    discount_price   = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    deposit_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text="% deposit required. Default 10% for treks, 100% for day trips."
    )

    # ── Safari / Beach Specifics ──────────────────────
    lodge_level = models.CharField(
        max_length=20, choices=LODGE_LEVEL_CHOICES, blank=True, null=True,
        help_text="For Safari tours: Define the comfort level."
    )
    beach_type  = models.CharField(
        max_length=20, choices=BEACH_TYPE_CHOICES, blank=True, null=True,
        help_text="For Beach tours: Define the vacation style."
    )

    # ── Details ───────────────────────────────────────
    duration_days = models.PositiveIntegerField()
    difficulty    = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    max_altitude  = models.CharField(max_length=100, blank=True)
    group_size    = models.CharField(max_length=50, blank=True)
    target_audience = models.CharField(max_length=200, blank=True)

    # ── Media ─────────────────────────────────────────
    feature_image = CloudinaryField(
        'image',
        folder='tours',
        transformation={'quality': 'auto:eco', 'fetch_format': 'auto'},
        validators=[validate_image_size, validate_image_format],
        null=True, blank=True,
        help_text=get_image_upload_help_text()
    )
    image_alt_text = models.CharField(max_length=150, blank=True)

    # ── SEO ───────────────────────────────────────────
    meta_title       = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=155, blank=True)
    focus_keyword    = models.CharField(max_length=100, blank=True)
    secondary_keywords = models.CharField(
        max_length=300, blank=True,
        help_text="Comma-separated LSI keywords e.g. 'safari lodges, best time for safari'"
    )
    canonical_url    = models.URLField(max_length=500, blank=True)
    og_title         = models.CharField(max_length=95, blank=True)
    og_description   = models.TextField(max_length=200, blank=True)
    og_image         = CloudinaryField(
        'image',
        folder='tours/og-images',
        blank=True, null=True,
        transformation={'width': 1200, 'height': 630, 'crop': 'fill'},
        validators=[validate_image_size, validate_image_format],
    )
    twitter_card_type = models.CharField(
        max_length=50, default='summary_large_image',
        choices=[
            ('summary',             'Summary'),
            ('summary_large_image', 'Summary Large Image'),
        ]
    )
    schema_type     = models.CharField(
        max_length=50, default='TouristTrip', choices=SCHEMA_TYPE_CHOICES
    )
    structured_data = models.JSONField(
        default=dict, blank=True,
        help_text="Extra JSON-LD fields merged into schema output."
    )

    # ── Performance / indexing ────────────────────────
    seo_priority    = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="1=low, 10=critical — used for sitemap priority"
    )
    page_views      = models.PositiveIntegerField(default=0)
    last_seo_audit  = models.DateTimeField(null=True, blank=True)
    last_indexed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Last time Google Indexing API was pinged for this URL"
    )

    # ── Status ────────────────────────────────────────
    is_featured = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tours'
        ordering = ['-is_featured', '-created_at']
        indexes  = [
            models.Index(fields=['slug'],                  name='tour_slug_idx'),
            models.Index(fields=['is_active', 'is_featured'], name='tour_active_featured_idx'),
            models.Index(fields=['category', 'is_active'], name='tour_category_idx'),
            models.Index(fields=['tour_type'],             name='tour_type_idx'),
            models.Index(fields=['price_usd'],             name='tour_price_idx'),
            models.Index(fields=['duration_days'],         name='tour_duration_idx'),
            models.Index(fields=['focus_keyword'],         name='tour_focus_keyword_idx'),  # fast conflict detection on import
            models.Index(fields=['is_active', 'focus_keyword'], name='tour_active_focus_idx'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tours:detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_full_seo_schemas(self, request=None):
        """Entry point into the crazy SEO engine — returns rich list of schema.org dicts.
        Powered by content from seo-tour skill (meta, faq blocks, itinerary, structured_data)."""
        from apps.core.seo_engine import build_tour_schema
        return build_tour_schema(self, request)

    def has_complete_seo(self) -> bool:
        """Quick check for basic SEO completeness."""
        return bool(self.focus_keyword and self.meta_title and self.meta_description)

    @property
    def seo_score(self) -> int:
        """Naive SEO completeness score (0-100). Useful for admin lists and reports."""
        score = 0
        if self.focus_keyword:
            score += 25
        if self.meta_title and len(self.meta_title) <= 60:
            score += 25
        if self.meta_description and len(self.meta_description) <= 155:
            score += 25
        if self.content_blocks.filter(block_type='faq').exists():
            score += 25
        return min(score, 100)  # cap at 100

    def get_focus_keyword_or_fallback(self):
        """Return focus keyword or derived from title for robust SEO."""
        if self.focus_keyword:
            return self.focus_keyword
        return slugify(self.title).replace('-', ' ')[:80]

    def is_premium_price(self):
        return (self.price_usd or 0) >= 2000

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while Tour.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tours:tour_detail', kwargs={'slug': self.slug})

    def get_structured_data(self):
        """
        Generate JSON-LD structured data for Google Rich Results.
        Targets TouristTrip and Product schemas.
        """
        from django.conf import settings
        domain = getattr(settings, 'SITE_DOMAIN', 'safari pro.com')
        url = f"https://{domain}{self.get_absolute_url()}"

        # Base TouristTrip / Product schema
        data = {
            "@context": "https://schema.org",
            "@type": self.schema_type,
            "name": self.title,
            "description": self.meta_description or self.excerpt,
            "url": url,
            "image": self.feature_image.url if self.feature_image else "",
            "touristType": self.target_audience or "Adventure travelers",
            "itinerary": [
                {
                    "@type": "City",
                    "name": self.place_name
                }
            ],
            "offers": {
                "@type": "Offer",
                "price": str(self.final_price),
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
                "url": url
            }
        }

        # Add AggregateRating if reviews exist
        avg = self.average_rating
        count = self.total_reviews
        if avg and count:
            data["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(avg),
                "reviewCount": str(count),
                "bestRating": "5",
                "worstRating": "1"
            }
            # Note: Do NOT include 'itemReviewed' here when nested inside Product/TouristTrip

        # Add tour-specific details
        if self.tour_type == 'safari' and self.lodge_level:
            data["touristType"] = f"{self.get_lodge_level_display()} Safari"

        # Merge manually added structured data
        if self.structured_data:
            data.update(self.structured_data)

        return data

    def get_breadcrumb_schema(self):
        """
        Generate BreadcrumbList JSON-LD.
        """
        from django.conf import settings
        domain = getattr(settings, 'SITE_DOMAIN', 'safari pro.com')
        base_url = f"https://{domain}"

        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": base_url
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Tours",
                    "item": f"{base_url}/tours/"
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": self.title,
                    "item": f"{base_url}{self.get_absolute_url()}"
                }
            ]
        }

    # ── Properties ───────────────────────────────────

    @property
    def final_price(self):
        return self.discount_price or self.price_usd

    @property
    def duration_label(self):
        return f"{self.duration_days} day{'s' if self.duration_days != 1 else ''}"

    @property
    def average_rating(self):
        """Pulls from reviews app via related_name='tour_reviews'"""
        agg = self.tour_reviews.filter(
            is_approved=True
        ).aggregate(models.Avg('rating'))
        avg = agg.get('rating__avg')
        return round(avg, 1) if avg else None

    @property
    def total_reviews(self):
        return self.tour_reviews.filter(is_approved=True).count()

    def calculate_costs(self, num_people, travel_date=None):
        from decimal import Decimal
        from datetime import date, datetime

        GATEWAY_FEE_RATE = Decimal('4.5')
        DAYS_THRESHOLD   = 10

        price_per_person = self.final_price
        subtotal         = price_per_person * num_people

        requires_full_payment = False
        days_until = None

        if travel_date:
            today = date.today()
            if isinstance(travel_date, datetime):
                travel_date = travel_date.date()
            days_until = (travel_date - today).days
            if days_until <= DAYS_THRESHOLD:
                requires_full_payment = True

        if requires_full_payment:
            deposit_pct    = Decimal('100.00')
            deposit_amount = subtotal
            balance        = Decimal('0.00')
            payment_type   = 'full_payment'
        else:
            deposit_pct    = self.deposit_percentage
            deposit_amount = (subtotal * deposit_pct) / 100
            balance        = subtotal - deposit_amount
            payment_type   = 'deposit'

        gateway_fee      = (deposit_amount * GATEWAY_FEE_RATE) / 100
        total_to_pay_now = deposit_amount + gateway_fee

        return {
            'price_per_person':       float(price_per_person),
            'num_people':             num_people,
            'subtotal':               float(subtotal),
            'deposit_percentage':     float(deposit_pct),
            'deposit_amount':         float(deposit_amount),
            'gateway_fee_rate':       float(GATEWAY_FEE_RATE),
            'gateway_fee':            float(gateway_fee),
            'total_to_pay_now':       float(total_to_pay_now),
            'balance_cash_on_arrival':float(balance),
            'total_trip_cost':        float(subtotal + gateway_fee),
            'tour_type':              self.get_tour_type_display(),
            'days_until_departure':   days_until,
            'requires_full_payment':  requires_full_payment,
            'payment_type':           payment_type,
            'booking_threshold_days': DAYS_THRESHOLD,
        }


# ============================================================
# TOUR GALLERY
# ============================================================

class TourImage(models.Model):
    tour      = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name='gallery'
    )
    image     = CloudinaryField(
        'image',
        folder='tours/gallery',
        transformation={'fetch_format': 'auto', 'quality': 'auto'},
        validators=[validate_image_size, validate_image_format],
        help_text=get_image_upload_help_text()
    )
    alt_text  = models.CharField(max_length=150, blank=True)
    caption   = models.CharField(max_length=255, blank=True)
    order     = models.PositiveIntegerField(default=0)
    is_hero   = models.BooleanField(default=False)

    class Meta:
        db_table = 'tour_images'
        ordering = ['tour', 'order']
        indexes  = [
            models.Index(fields=['tour'],    name='tourimage_tour_idx'),
            models.Index(fields=['is_hero'], name='tourimage_hero_idx'),
        ]

    def __str__(self):
        return f"{self.tour.title} — {self.caption or self.alt_text or 'Image'}"


# ============================================================
# SEASONAL WINDOW
# ============================================================

class SeasonalWindow(models.Model):
    RATING_CHOICES = [
        ('best',     'Best Season'),
        ('good',     'Good'),
        ('possible', 'Possible'),
        ('avoid',    'Avoid'),
    ]

    tour        = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name='seasonal_windows'
    )
    month_start = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    month_end   = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    rating      = models.CharField(max_length=10, choices=RATING_CHOICES)
    notes       = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'tour_seasonal_windows'
        ordering = ['tour', 'month_start']
        indexes  = [
            models.Index(fields=['tour'],        name='seasonal_tour_idx'),
            models.Index(fields=['month_start'], name='seasonal_month_idx'),
        ]

    def __str__(self):
        return f"{self.tour.title} — months {self.month_start}–{self.month_end} ({self.rating})"


# ============================================================
# TOUR CONTENT BLOCKS (CMS — same pattern as guide app)
# ============================================================

class TourContentBlock(models.Model):
    BLOCK_TYPE_CHOICES = [
        ('heading',       'Heading (H2)'),
        ('subheading',    'Subheading (H3)'),
        ('paragraph',     'Paragraph'),
        ('faq',           'FAQ Item'),
        ('highlight_box', 'Highlight Box'),
        ('cta_block',     'Call-to-Action Block'),
        ('list',          'Bullet List'),
        ('quote',         'Pull Quote'),
    ]

    tour        = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name='content_blocks'
    )
    block_type  = models.CharField(
        max_length=20, choices=BLOCK_TYPE_CHOICES, default='paragraph'
    )
    heading     = models.CharField(max_length=200, blank=True)
    content     = CKEditor5Field(config_name='extends', blank=True)
    order       = models.PositiveIntegerField(default=0)
    anchor_id   = models.SlugField(
        max_length=80, blank=True,
        help_text="Auto-generated from heading for TOC links"
    )
    focus_keyword   = models.CharField(max_length=100, blank=True)
    include_in_toc  = models.BooleanField(
        default=True,
        help_text="Include this heading in the table of contents"
    )

    class Meta:
        db_table = 'tour_content_blocks'
        ordering = ['tour', 'order']
        indexes  = [
            models.Index(fields=['tour', 'order'], name='contentblock_tour_order_idx'),
        ]

    def __str__(self):
        return f"{self.tour.title} — {self.get_block_type_display()} ({self.order})"

    def save(self, *args, **kwargs):
        if self.heading and not self.anchor_id:
            self.anchor_id = slugify(self.heading)[:80]
        super().save(*args, **kwargs)


# ============================================================
# COMBO PACKAGE (new product — mountain + safari + beach)
# ============================================================

class ComboPackage(models.Model):
    title       = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True, blank=True)
    description = CKEditor5Field(config_name='extends')
    excerpt     = models.TextField(max_length=300, blank=True)
    tours       = models.ManyToManyField(
        Tour, related_name='combo_packages', blank=True
    )
    total_price  = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days= models.PositiveIntegerField()
    featured_image = CloudinaryField(
        'image', folder='combos',
        transformation={'fetch_format': 'auto', 'quality': 'auto'},
        blank=True, null=True
    )
    tags        = models.ManyToManyField(
        Tag, related_name='combo_packages', blank=True
    )

    # SEO
    meta_title       = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=155, blank=True)
    focus_keyword    = models.CharField(max_length=100, blank=True)
    schema_type      = models.CharField(max_length=50, default='TouristTrip')
    last_indexed_at  = models.DateTimeField(null=True, blank=True)

    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'combo_packages'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['slug'],      name='combo_slug_idx'),
            models.Index(fields=['is_active'], name='combo_active_idx'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while ComboPackage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tours:combo_detail', kwargs={'slug': self.slug})

    @property
    def price_usd(self):
        return self.total_price

    @property
    def total_duration(self):
        return self.duration_days

    @property
    def feature_image(self):
        return self.featured_image

    @property
    def savings_amount(self):
        from decimal import Decimal
        individual_total = sum((t.price_usd for t in self.tours.all()), Decimal('0'))
        return max(individual_total - self.total_price, Decimal('0'))


# ============================================================
# TOUR AVAILABILITY (standalone date slots — not group)
# ============================================================

class TourAvailability(models.Model):
    STATUS_CHOICES = [
        ('open',      'Open'),
        ('sold_out',  'Sold Out'),
        ('cancelled', 'Cancelled'),
        ('pending',   'Pending'),
    ]

    tour        = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name='availabilities'
    )
    start_date  = models.DateTimeField()
    end_date    = models.DateTimeField()
    capacity    = models.PositiveIntegerField()
    booked_count= models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    status      = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open'
    )
    created_by  = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_availabilities'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'tour_availability'
        ordering            = ['start_date']
        verbose_name        = 'Tour Availability'
        verbose_name_plural = 'Tour Availabilities'
        indexes             = [
            models.Index(fields=['tour', 'status'],        name='avail_tour_status_idx'),
            models.Index(fields=['start_date', 'status'],  name='avail_date_status_idx'),
        ]

    def __str__(self):
        return f"{self.tour.title} — {self.start_date.strftime('%b %d, %Y')}"

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date.")
        if self.booked_count > self.capacity:
            raise ValidationError("Booked count cannot exceed capacity.")

    def save(self, *args, **kwargs):
        if self.booked_count >= self.capacity and self.status == 'open':
            self.status = 'sold_out'
        super().save(*args, **kwargs)

    @property
    def spots_remaining(self):
        return max(0, self.capacity - self.booked_count)

    @property
    def is_available(self):
        return self.status == 'open' and self.spots_remaining > 0

    @property
    def effective_price(self):
        return self.price_override or self.tour.discount_price or self.tour.price_usd

    @property
    def fill_percentage(self):
        if not self.capacity:
            return 0
        return int((self.booked_count / self.capacity) * 100)

    def book_spots(self, num_spots):
        if self.spots_remaining < num_spots:
            raise ValidationError(f"Only {self.spots_remaining} spot(s) available.")
        self.booked_count += num_spots
        self.save()

        return int((self.booked_count / self.capacity) * 100)

    def book_spots(self, num_spots):
        if self.spots_remaining < num_spots:
            raise ValidationError(f"Only {self.spots_remaining} spot(s) available.")
        self.booked_count += num_spots
        self.save()
