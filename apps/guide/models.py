# apps/guide/models.py
# Trek guides, blog articles, and CMS content blocks.
# Full SEO mesh: semantic relations to tours via tags, keywords,
# excerpts, internal links, and structured cross-references.

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django_ckeditor_5.fields import CKEditor5Field
from cloudinary.models import CloudinaryField

User = get_user_model()


# ============================================================
# GUIDE CATEGORY
# ============================================================

class GuideCategory(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(
        max_length=50, blank=True,
        help_text="Lucide icon name e.g. 'mountain', 'backpack'"
    )
    # SEO for the category page
    meta_title      = models.CharField(max_length=60, blank=True)
    meta_description= models.CharField(max_length=155, blank=True)
    order       = models.IntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        db_table           = 'guide_categories'
        verbose_name_plural= 'Guide Categories'
        ordering           = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('guide:category', kwargs={'slug': self.slug})


# ============================================================
# TREK GUIDE
# Full SEO mesh — relations to Tour via:
#   - tags (shared topic clusters)
#   - related_tours M2M (direct cross-links)
#   - focus_keyword / secondary_keywords (semantic overlap)
#   - first_paragraph (Google uses this for entity understanding)
#   - internal links via GuideInternalLink
# ============================================================

class TrekGuide(models.Model):

    DIFFICULTY_CHOICES = [
        ('beginner',     'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced',     'Advanced'),
        ('all_levels',   'All Levels'),
    ]

    # ── Core content ─────────────────────────────────
    title       = models.CharField(
        max_length=200,
        help_text="Keep 55–60 chars for best SERP display"
    )
    slug        = models.SlugField(unique=True, blank=True)
    category    = models.ForeignKey(
        GuideCategory, on_delete=models.CASCADE, related_name='guides'
    )
    author      = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='trek_guides'
    )

    # ── SEO mesh fields ───────────────────────────────
    # first_paragraph is critical — Google extracts it for entity context
    # and it anchors semantic relations between this guide and tour pages
    first_paragraph = models.TextField(
        blank=True,
        help_text=(
            "Opening paragraph shown below the title. "
            "CRITICAL for SEO — include focus keyword naturally. "
            "Google uses this to understand page entity and topic."
        )
    )
    excerpt     = models.TextField(
        max_length=300, blank=True,
        help_text="155–300 chars. Used in cards, meta description fallback, and related content previews."
    )
    content     = CKEditor5Field(
        config_name='extends',
        help_text="Full guide body. first_paragraph is rendered separately above this."
    )

    # ── Tags — shared with tours for topic clustering ─
    tags        = models.ManyToManyField(
        'tours.Tag',
        blank=True,
        related_name='trek_guides',
        help_text=(
            "Shared tags with Tour model — creates topic cluster mesh. "
            "e.g. tag 'machame-route' links this guide to all Machame tours."
        )
    )

    # ── Direct tour relations ─────────────────────────
    related_tours = models.ManyToManyField(
        'tours.Tour',
        blank=True,
        related_name='related_guides',
        help_text="Tours directly related to this guide — shown as CTAs at bottom of guide"
    )
    primary_tour = models.ForeignKey(
        'tours.Tour',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='primary_guides',
        help_text=(
            "The single most relevant tour for this guide. "
            "Used for the main booking CTA and canonical cross-link."
        )
    )

    # ── SEO fields ────────────────────────────────────
    meta_title          = models.CharField(max_length=60, blank=True)
    meta_description    = models.CharField(max_length=155, blank=True)
    focus_keyword       = models.CharField(
        max_length=100, blank=True,
        help_text="Primary keyword — should appear in title, first_paragraph, and meta_description"
    )
    secondary_keywords  = models.CharField(
        max_length=300, blank=True,
        help_text="Comma-separated secondary/LSI keywords e.g. 'machame route map, machame route distance'"
    )
    canonical_url       = models.URLField(max_length=500, blank=True)
    og_title            = models.CharField(max_length=95, blank=True)
    og_description      = models.TextField(max_length=200, blank=True)
    og_image            = CloudinaryField(
        'image', folder='guides/og-images',
        blank=True, null=True,
        transformation={'width': 1200, 'height': 630, 'crop': 'fill', 'fetch_format': 'auto'}
    )
    schema_type         = models.CharField(
        max_length=50, default='Article',
        choices=[
            ('Article',    'Article'),
            ('HowTo',      'How-To Guide'),
            ('FAQPage',    'FAQ Page'),
            ('BlogPosting','Blog Post'),
        ]
    )

    # ── Media ─────────────────────────────────────────
    featured_image  = CloudinaryField(
        'image', folder='guides',
        transformation={'fetch_format': 'auto', 'quality': 'auto'},
        null=True, blank=True
    )
    image_alt_text  = models.CharField(max_length=150, blank=True)

    # ── Difficulty / context ──────────────────────────
    difficulty      = models.CharField(
        max_length=20, choices=DIFFICULTY_CHOICES,
        blank=True, default='all_levels'
    )

    # ── Publishing ────────────────────────────────────
    is_published    = models.BooleanField(default=False)
    is_featured     = models.BooleanField(default=False)
    publish_date    = models.DateTimeField(default=timezone.now)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    # ── Engagement + indexing ─────────────────────────
    view_count      = models.PositiveIntegerField(default=0)
    reading_time    = models.PositiveIntegerField(
        default=5, help_text="Auto-calculated. Minutes to read."
    )
    last_indexed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Last Google Indexing API ping"
    )

    class Meta:
        db_table            = 'trek_guides'
        ordering            = ['-publish_date']
        verbose_name        = 'Trek Guide'
        verbose_name_plural = 'Trek Guides'
        indexes             = [
            models.Index(fields=['slug'],                       name='guide_slug_idx'),
            models.Index(fields=['is_published', 'is_featured'],name='guide_pub_feat_idx'),
            models.Index(fields=['category', 'is_published'],   name='guide_cat_pub_idx'),
            models.Index(fields=['publish_date'],               name='guide_date_idx'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while TrekGuide.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        # Auto-excerpt from first_paragraph or content
        if not self.excerpt:
            from django.utils.html import strip_tags
            source = self.first_paragraph or self.content or ''
            clean = strip_tags(source)
            self.excerpt = clean[:297] + '...' if len(clean) > 297 else clean

        # Auto reading time
        if self.content:
            from django.utils.html import strip_tags
            words = len(strip_tags(self.content).split())
            self.reading_time = max(1, round(words / 200))

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('guide:detail', kwargs={'slug': self.slug})

    def get_structured_data(self):
        """
        Generate JSON-LD for Article / HowTo.
        """
        from django.conf import settings
        domain = getattr(settings, 'SITE_DOMAIN', 'visitkili.com')
        url = f"https://{domain}{self.get_absolute_url()}"
        
        return {
            "@context": "https://schema.org",
            "@type": self.schema_type,
            "headline": self.title,
            "description": self.meta_description or self.excerpt,
            "image": self.featured_image.url if self.featured_image else "",
            "author": {
                "@type": "Person",
                "name": self.author.get_full_name() if self.author else "VisitKili Team"
            },
            "publisher": {
                "@type": "Organization",
                "name": "VISIT KILI ADVENTURES",
                "logo": {
                    "@type": "ImageObject",
                    "url": f"https://{domain}/static/images/logo.png"
                }
            },
            "datePublished": self.publish_date.isoformat(),
            "dateModified": self.updated_at.isoformat()
        }

    def get_breadcrumb_schema(self):
        """
        Generate BreadcrumbList JSON-LD.
        """
        from django.conf import settings
        domain = getattr(settings, 'SITE_DOMAIN', 'visitkili.com')
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
                    "name": "Guides",
                    "item": f"{base_url}/guides/trekking-guides/"
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": self.title,
                    "item": f"{base_url}{self.get_absolute_url()}"
                }
            ]
        }

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.excerpt

    def increment_view_count(self):
        TrekGuide.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )

    # ── SEO mesh helpers ──────────────────────────────

    def get_shared_tags_with_tour(self, tour):
        """Tags this guide shares with a specific tour — used for mesh highlighting."""
        return self.tags.filter(pk__in=tour.tags.all())

    def get_secondary_keywords_list(self):
        """Return secondary_keywords as a list."""
        if not self.secondary_keywords:
            return []
        return [k.strip() for k in self.secondary_keywords.split(',') if k.strip()]


# ============================================================
# BLOG ARTICLE
# Same mesh pattern as TrekGuide — relates to tours via
# tags, related_tours, focus_keyword, first_paragraph
# ============================================================

class BlogArticle(models.Model):

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('archived',  'Archived'),
    ]

    # ── Core content ─────────────────────────────────
    title           = models.CharField(max_length=200)
    slug            = models.SlugField(unique=True, blank=True)
    category        = models.ForeignKey(
        GuideCategory, on_delete=models.CASCADE, related_name='articles'
    )
    author          = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='blog_articles'
    )

    # ── SEO mesh fields ───────────────────────────────
    first_paragraph = models.TextField(
        blank=True,
        help_text=(
            "Opening paragraph — rendered prominently above main content. "
            "Include focus keyword naturally. Critical for Google entity understanding."
        )
    )
    excerpt         = models.TextField(
        max_length=300, blank=True,
        help_text="Used in article cards, meta description fallback, and related content previews."
    )
    content         = CKEditor5Field(config_name='extends')

    # ── Tour relations — mesh network ─────────────────
    related_tours   = models.ManyToManyField(
        'tours.Tour',
        blank=True,
        related_name='blog_articles',
        help_text="Tours mentioned or relevant to this article — renders as related CTAs"
    )
    primary_tour    = models.ForeignKey(
        'tours.Tour',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='primary_articles',
        help_text="Main tour CTA shown at end of article"
    )
    related_guides  = models.ManyToManyField(
        TrekGuide,
        blank=True,
        related_name='related_articles',
        help_text="Trek guides to show as 'Further Reading' — strengthens internal mesh"
    )
    tags            = models.ManyToManyField(
        'tours.Tag',
        blank=True,
        related_name='blog_articles',
        help_text="Shared tag taxonomy with tours and guides — topic cluster foundation"
    )

    # ── SEO fields ────────────────────────────────────
    meta_title          = models.CharField(max_length=60, blank=True)
    meta_description    = models.CharField(max_length=155, blank=True)
    focus_keyword       = models.CharField(max_length=100, blank=True)
    secondary_keywords  = models.CharField(
        max_length=300, blank=True,
        help_text="Comma-separated LSI keywords"
    )
    canonical_url       = models.URLField(max_length=500, blank=True)
    og_title            = models.CharField(max_length=95, blank=True)
    og_description      = models.TextField(max_length=200, blank=True)
    og_image            = CloudinaryField(
        'image', folder='blog/og-images',
        blank=True, null=True,
        transformation={'width': 1200, 'height': 630, 'crop': 'fill', 'fetch_format': 'auto'}
    )
    schema_type         = models.CharField(
        max_length=50, default='BlogPosting',
        choices=[
            ('BlogPosting', 'Blog Post'),
            ('Article',     'Article'),
            ('NewsArticle', 'News Article'),
        ]
    )

    # ── Media ─────────────────────────────────────────
    featured_image  = CloudinaryField(
        'image', folder='blog',
        transformation={'fetch_format': 'auto', 'quality': 'auto'},
        null=True, blank=True
    )
    image_alt_text  = models.CharField(max_length=150, blank=True)

    # ── Publishing ────────────────────────────────────
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    publish_date    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    # ── Engagement + indexing ─────────────────────────
    view_count      = models.PositiveIntegerField(default=0)
    reading_time    = models.PositiveIntegerField(default=5)
    last_indexed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table            = 'blog_articles'
        ordering            = ['-publish_date']
        verbose_name        = 'Blog Article'
        verbose_name_plural = 'Blog Articles'
        indexes             = [
            models.Index(fields=['slug'],                   name='article_slug_idx'),
            models.Index(fields=['status', 'publish_date'], name='article_status_date_idx'),
            models.Index(fields=['category', 'status'],     name='article_cat_status_idx'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while BlogArticle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        if self.status == 'published' and not self.publish_date:
            self.publish_date = timezone.now()

        if not self.excerpt:
            from django.utils.html import strip_tags
            source = self.first_paragraph or self.content or ''
            clean = strip_tags(source)
            self.excerpt = clean[:297] + '...' if len(clean) > 297 else clean

        if self.content:
            from django.utils.html import strip_tags
            words = len(strip_tags(self.content).split())
            self.reading_time = max(1, round(words / 200))

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('guide:article_detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.excerpt

    def increment_view_count(self):
        BlogArticle.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )

    def get_secondary_keywords_list(self):
        if not self.secondary_keywords:
            return []
        return [k.strip() for k in self.secondary_keywords.split(',') if k.strip()]


# ============================================================
# GUIDE CONTENT BLOCK — same CMS pattern as TourContentBlock
# ============================================================

class GuideContentBlock(models.Model):

    BLOCK_TYPE_CHOICES = [
        ('heading',      'Heading (H2)'),
        ('subheading',   'Subheading (H3)'),
        ('paragraph',    'Paragraph'),
        ('list',         'Bullet List'),
        ('numbered_list','Numbered List'),
        ('quote',        'Pull Quote'),
        ('warning',      'Warning / Alert'),
        ('info',         'Info Box'),
        ('checklist',    'Checklist'),
        ('faq',          'FAQ Item'),
        ('highlight_box','Highlight Box'),
        ('cta_block',    'Call-to-Action Block'),
    ]

    guide       = models.ForeignKey(
        TrekGuide, on_delete=models.CASCADE, related_name='content_blocks'
    )
    block_type  = models.CharField(
        max_length=20, choices=BLOCK_TYPE_CHOICES, default='paragraph'
    )
    heading     = models.CharField(max_length=300, blank=True)
    content     = CKEditor5Field(config_name='extends', blank=True)
    order       = models.PositiveIntegerField(default=0)
    include_in_toc = models.BooleanField(default=True)
    anchor_id   = models.SlugField(max_length=100, blank=True)
    focus_keyword = models.CharField(
        max_length=100, blank=True,
        help_text="Target keyword for this specific section — aids semantic SEO"
    )
    icon        = models.CharField(
        max_length=50, blank=True,
        help_text="Lucide icon name for this block"
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'guide_content_blocks'
        ordering            = ['guide', 'order']
        verbose_name        = 'Guide Content Block'
        verbose_name_plural = 'Guide Content Blocks'
        indexes             = [
            models.Index(fields=['guide', 'order'], name='guideblock_guide_order_idx'),
        ]

    def __str__(self):
        return f"{self.guide.title} — {self.get_block_type_display()} ({self.order})"

    def save(self, *args, **kwargs):
        if self.heading and not self.anchor_id:
            base = slugify(self.heading)
            anchor = base
            n = 1
            while GuideContentBlock.objects.filter(
                guide=self.guide, anchor_id=anchor
            ).exclude(pk=self.pk).exists():
                anchor = f"{base}-{n}"
                n += 1
            self.anchor_id = anchor
        super().save(*args, **kwargs)


# ============================================================
# GUIDE INTERNAL LINK
# Cross-links between guides + to tours — mesh backbone
# ============================================================

class GuideInternalLink(models.Model):

    LINK_TYPE_CHOICES = [
        ('related',      'Related Guide'),
        ('prerequisite', 'Prerequisite Reading'),
        ('next_step',    'Next Step'),
        ('detailed',     'More Details'),
        ('tour',         'Related Tour'),
    ]

    from_guide  = models.ForeignKey(
        TrekGuide, on_delete=models.CASCADE, related_name='outgoing_links'
    )
    # Links to another guide OR directly to a tour page
    to_guide    = models.ForeignKey(
        TrekGuide, on_delete=models.CASCADE,
        related_name='incoming_links',
        null=True, blank=True
    )
    to_tour     = models.ForeignKey(
        'tours.Tour', on_delete=models.CASCADE,
        related_name='guide_links',
        null=True, blank=True,
        help_text="Link directly to a tour product page — guide → tour backlink"
    )
    to_url      = models.URLField(
        max_length=500, blank=True,
        help_text="External URL only if not linking to a guide or tour"
    )
    anchor_text = models.CharField(
        max_length=200,
        help_text="Visible link text — include target keyword for SEO value"
    )
    link_type   = models.CharField(
        max_length=20, choices=LINK_TYPE_CHOICES, default='related'
    )
    is_nofollow = models.BooleanField(
        default=False,
        help_text="Add rel='nofollow' — use for external/affiliate links only"
    )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table            = 'guide_internal_links'
        verbose_name        = 'Guide Internal Link'
        verbose_name_plural = 'Guide Internal Links'
        ordering            = ['-created_at']
        indexes             = [
            models.Index(fields=['from_guide', 'is_active'], name='glink_from_active_idx'),
            models.Index(fields=['to_guide'],                name='glink_to_guide_idx'),
            models.Index(fields=['to_tour'],                 name='glink_to_tour_idx'),
        ]

    def __str__(self):
        dest = self.to_guide or self.to_tour or self.to_url
        return f"{self.from_guide.title} → {dest}"

    def clean(self):
        targets = [self.to_guide, self.to_tour, self.to_url]
        filled = [t for t in targets if t]
        if not filled:
            raise ValidationError("Specify to_guide, to_tour, or to_url.")
        if len(filled) > 1:
            raise ValidationError("Specify only one of to_guide, to_tour, or to_url.")
        if self.to_guide and self.to_guide == self.from_guide:
            raise ValidationError("Cannot link a guide to itself.")

    def get_link_url(self):
        if self.to_guide:
            return self.to_guide.get_absolute_url()
        if self.to_tour:
            return self.to_tour.get_absolute_url()
        return self.to_url

    def get_rel_attribute(self):
        return 'nofollow' if self.is_nofollow else ''
