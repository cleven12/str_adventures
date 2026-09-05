# config/urls.py — Structured Adventures
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.core.sitemaps import (
    StaticSitemap, TourSitemap, ComboSitemap,
    GuideSitemap, ArticleSitemap, TagSitemap, DestinationSitemap
)
from config.api_urls import api_urlpatterns

handler400 = 'apps.core.views.custom_400'
handler403 = 'apps.core.views.custom_403'
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'

sitemaps = {
    'static':       StaticSitemap,
    'tours':        TourSitemap,
    'combos':       ComboSitemap,
    'guides':       GuideSitemap,
    'articles':     ArticleSitemap,
    'tags':         TagSitemap,
    'destinations': DestinationSitemap,
}

urlpatterns = [
    path('admin/',        admin.site.urls),
    path('ckeditor5/',    include('django_ckeditor_5.urls')),
    path('sitemap.xml',   sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('api/v1/',       include(api_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
