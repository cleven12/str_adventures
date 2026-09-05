from django.contrib.sitemaps import Sitemap
from apps.tours.models import Tour, Tag, ComboPackage
from apps.guide.models import TrekGuide, BlogArticle
from apps.destinations.models import Destination
from django.db.models import Q

class StaticSitemap(Sitemap):
    """
    Static frontend page paths — hardcoded rather than reverse()'d, since
    these pages are served by the Next.js frontend, not this API backend.
    """
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return [
            '/',
            '/about/',
            '/contact/',
            '/faq/',
            '/tours/',
            '/tours/search/',
            '/tours/category/',
            '/guides/trekking-guides/',
            '/guides/articles/',
            '/destinations/',
            '/booking/groups/',
            '/reviews/',
        ]

    def location(self, item):
        return item

class TourSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Tour.objects.filter(is_active=True).order_by('-seo_priority', '-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        # Convert seo_priority (1-10) to 0.1-1.0
        return float(obj.seo_priority) / 10.0

class ComboSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ComboPackage.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

class GuideSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return TrekGuide.objects.filter(is_published=True).order_by('-publish_date')

    def lastmod(self, obj):
        return obj.updated_at

class ArticleSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return BlogArticle.objects.filter(status='published').order_by('-publish_date')

    def lastmod(self, obj):
        return obj.updated_at

class TagSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        # Only show tags that have active tours or guides
        return Tag.objects.filter(is_active=True).filter(
            Q(tours__is_active=True) | Q(trek_guides__is_published=True)
        ).distinct()


class DestinationSitemap(Sitemap):
    priority = 0.65
    changefreq = "monthly"

    def items(self):
        return Destination.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        # Higher for featured destinations
        return 0.8 if getattr(obj, 'is_featured', False) else 0.65
