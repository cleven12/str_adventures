from django.db import models
from cloudinary.models import CloudinaryField

class DestinationCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Destination Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class Destination(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(DestinationCategory, on_delete=models.SET_NULL, null=True, related_name='destinations')
    
    # Content
    short_description = models.TextField(help_text="For list views and meta descriptions.")
    description = models.TextField(help_text="Main content, supports HTML/Safe.")
    
    # Visuals
    feature_image = CloudinaryField('image', blank=True, null=True)
    
    # Metadata
    location_name = models.CharField(max_length=200, blank=True, help_text="e.g. Serengeti National Park, Tanzania")
    altitude = models.CharField(max_length=50, blank=True)
    best_time_to_visit = models.CharField(max_length=200, blank=True)
    
    # Mesh Network / Backlinks
    related_tours = models.ManyToManyField('tours.Tour', blank=True, related_name='mentioned_in_destinations')
    related_guides = models.ManyToManyField('guide.TrekGuide', blank=True, related_name='mentioned_in_destinations')
    related_articles = models.ManyToManyField('guide.BlogArticle', blank=True, related_name='mentioned_in_destinations')
    tags = models.ManyToManyField('tours.Tag', blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=100, blank=True)
    meta_description = models.TextField(blank=True)
    focus_keyword = models.CharField(max_length=100, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_indexed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Last time Google Indexing API was pinged for this URL"
    )

    @property
    def seo_score(self):
        """Lightweight SEO health score for admin and reports (0-100)."""
        score = 40
        if self.focus_keyword:
            score += 20
        if self.meta_title:
            score += 15
        if self.meta_description:
            score += 15
        if self.short_description and len(self.short_description) > 40:
            score += 10
        return min(100, score)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/destinations/{self.slug}/"

    def has_complete_seo(self) -> bool:
        return bool(self.focus_keyword and self.meta_title and self.meta_description)

    @property
    def seo_score(self) -> int:
        score = 0
        if self.focus_keyword:
            score += 30
        if self.meta_title:
            score += 30
        if self.meta_description:
            score += 20
        if self.faqs.exists():
            score += 20
        return min(score, 100)

class DestinationGallery(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='gallery')
    image = CloudinaryField('image')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class DestinationFAQ(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
