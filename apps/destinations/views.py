from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from .models import Destination, DestinationCategory
from apps.core.seo_engine import get_destination_schemas, build_destination_schema


@cache_page(60 * 30)
def destination_list(request):
    destinations = Destination.objects.filter(is_active=True).select_related('category').only('id', 'name', 'slug', 'short_description', 'feature_image', 'category_id', 'focus_keyword')
    categories = DestinationCategory.objects.all()
    return render(request, 'destinations/list.html', {
        'destinations': destinations,
        'categories': categories,
        'meta_title': 'Explore Tanzania Destinations | VISIT KILI ADVNTURES',
        'meta_description': 'Discover top attractions in Tanzania from Serengeti to Zanzibar and Kilimanjaro routes. Expert local Moshi operator.',
        'json_ld': None,  # list can use ItemList if wanted
    })


def destination_detail(request, slug):
    destination = get_object_or_404(
        Destination.objects.prefetch_related(
            'gallery', 'faqs', 'related_tours', 'related_guides', 'related_articles', 'tags'
        ).defer('description'),  # defer heavy text until needed
        slug=slug, is_active=True
    )

    # CRAZY rich schema powered by seo-destination skill imports (faqs + meta)
    schema_json = get_destination_schemas(destination, request)
    # Also expose raw for debugging / extra blocks
    raw_schemas = build_destination_schema(destination, request)

    # Proper SEO context (template already uses some)
    meta_title = destination.meta_title or f"{destination.name} | Tanzania Travel Guide"
    meta_desc = destination.meta_description or destination.short_description

    return render(request, 'destinations/detail.html', {
        'destination': destination,
        'meta_title': meta_title,
        'meta_description': meta_desc,
        'json_ld': schema_json,           # rendered in block schema
        'schemas': raw_schemas,           # if template wants to extend
    })


def category_detail(request, slug):
    category = get_object_or_404(DestinationCategory, slug=slug)
    destinations = category.destinations.filter(is_active=True)
    return render(request, 'destinations/category.html', {
        'category': category,
        'destinations': destinations,
    })
