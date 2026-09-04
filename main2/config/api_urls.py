# config/api_urls.py
# All API routes — include this in config/urls.py under path('api/v1/', ...)
#
# Add to config/urls.py:
#   from config.api_urls import api_urlpatterns
#   urlpatterns += [path('api/v1/', include(api_urlpatterns))]

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.api_views import (
    # Aggregated
    HomepageView,
    GlobalSearchView,
    # Slug lists (Next.js generateStaticParams)
    TourSlugListView, GuideSlugListView, ArticleSlugListView,
    DestinationSlugListView, TagSlugListView, ComboSlugListView,
    # ViewSets
    TourViewSet, TagViewSet, TourCategoryViewSet, ComboViewSet,
    TrekGuideViewSet, BlogArticleViewSet, GuideCategoryViewSet,
    DestinationViewSet, ReviewViewSet, GroupDepartureViewSet,
    FAQViewSet,
    # Simple views
    SiteSettingsView, TeamView, CareersView,
)

router = DefaultRouter()
router.register("tours",            TourViewSet,            basename="tour")
router.register("tags",             TagViewSet,             basename="tag")
router.register("categories",       TourCategoryViewSet,    basename="category")
router.register("combos",           ComboViewSet,           basename="combo")
router.register("guides",           TrekGuideViewSet,       basename="guide")
router.register("articles",         BlogArticleViewSet,     basename="article")
router.register("guide-categories", GuideCategoryViewSet,   basename="guide-category")
router.register("destinations",     DestinationViewSet,     basename="destination")
router.register("reviews",          ReviewViewSet,          basename="review")
router.register("group-departures", GroupDepartureViewSet,  basename="group-departure")
router.register("faqs",             FAQViewSet,             basename="faq")

api_urlpatterns = [
    # Router endpoints
    path("", include(router.urls)),

    # Aggregated / special
    path("homepage/",  HomepageView.as_view(),     name="api-homepage"),
    path("search/",    GlobalSearchView.as_view(),  name="api-search"),
    path("site/",      SiteSettingsView.as_view(),  name="api-site"),
    path("team/",      TeamView.as_view(),           name="api-team"),
    path("careers/",   CareersView.as_view(),        name="api-careers"),

    # Slug lists for Next.js static generation
    path("slugs/tours/",        TourSlugListView.as_view(),        name="slugs-tours"),
    path("slugs/guides/",       GuideSlugListView.as_view(),       name="slugs-guides"),
    path("slugs/articles/",     ArticleSlugListView.as_view(),     name="slugs-articles"),
    path("slugs/destinations/", DestinationSlugListView.as_view(), name="slugs-destinations"),
    path("slugs/tags/",         TagSlugListView.as_view(),         name="slugs-tags"),
    path("slugs/combos/",       ComboSlugListView.as_view(),       name="slugs-combos"),
]
