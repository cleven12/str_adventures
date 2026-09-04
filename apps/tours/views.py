import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Min, Max
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .models import (
    Tour, TourCategory, Tag, ComboPackage,
    TourAvailability,
)


# ── Helpers ───────────────────────────────────────────────

_SEARCH_STOPWORDS = {'and', 'the', 'to', 'for', 'of', 'in', 'on', 'a', 'an',
                     'with', 'vs', 'or', 'is', 'are', 'my', 'we', 'i'}


def _kw_q(q, fields, op='AND'):
    """Tokenized keyword query: each query word is matched across `fields`
    (OR across fields). With op='AND' every word must match (precision); with
    op='OR' any word matches (recall). This lets keyword-tags match varied
    phrasings — e.g. "serengeti ngorongoro safari" matches a tour tagged
    `serengeti ngorongoro` plus `safari` elsewhere, even though no single field
    holds the whole phrase.
    """
    import re
    from django.db.models import Q
    q = (q or '').strip()
    if not q:
        return Q()
    tokens = [t for t in re.split(r'\s+', q.lower())
              if len(t) >= 3 and t not in _SEARCH_STOPWORDS]
    if not tokens:
        tokens = [q.lower()]
    combined = None
    for tok in tokens:
        any_field = Q()
        for f in fields:
            any_field |= Q(**{f + '__icontains': tok})
        if combined is None:
            combined = any_field
        elif op == 'OR':
            combined |= any_field
        else:
            combined &= any_field
    return combined


def _kw_filter(qs, q, fields):
    """Apply tokenized AND match for precision; if nothing matches, fall back to
    OR so the user still gets relevant content back instead of an empty page."""
    r = qs.filter(_kw_q(q, fields, 'AND')).distinct()
    if not r.exists():
        r = qs.filter(_kw_q(q, fields, 'OR')).distinct()
    return r


def _save_last_url(request):
    """Save current path for post-login redirect."""
    request.session['last_url'] = request.path


def _tours_queryset(request):
    """Base queryset — active tours, annotate rating."""
    qs = Tour.objects.filter(is_active=True).select_related(
        'category'
    ).prefetch_related(
        'tags', 'seasonal_windows', 'group_departures', 'gallery'
    ).only(
        'id', 'title', 'slug', 'place_name', 'duration_days', 'difficulty',
        'price_usd', 'excerpt', 'is_featured', 'category_id', 'focus_keyword'
    ).annotate(
        avg_rating=Avg('tour_reviews__rating'),
        review_count=Count('tour_reviews'),
    )

    # ── Filters from GET params ───────────────────────────
    types        = request.GET.getlist('type')
    difficulties = request.GET.getlist('difficulty')
    category     = request.GET.get('category')
    active_category = request.GET.get('category')
    duration     = request.GET.get('duration')
    month        = request.GET.getlist('month')  # Support multiple months
    min_price    = request.GET.get('min_price')
    max_price    = request.GET.get('max_price')
    q            = request.GET.get('q', '').strip()

    if types:
        qs = qs.filter(tour_type__in=types)
    if difficulties:
        # Check if it's a list or a single string (from radio or multiple checkboxes)
        if isinstance(difficulties, list) and difficulties[0] == '':
             pass # "All" selected
        else:
             qs = qs.filter(difficulty__in=[d for d in difficulties if d])
             
    if category:
        qs = qs.filter(category__slug=category)
        active_category = category
    if duration:
        if duration == '1-3':
            qs = qs.filter(duration_days__lte=3)
        elif duration == '4-7':
            qs = qs.filter(duration_days__range=(4, 7))
        elif duration == '8+':
            qs = qs.filter(duration_days__gte=8)
            
    if month:
        # Map month names (jan, feb...) to numbers if needed
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        month_nums = []
        for m in month:
            if m.isdigit():
                month_nums.append(int(m))
            elif m.lower() in month_map:
                month_nums.append(month_map[m.lower()])
        
        if month_nums:
            qs = qs.filter(
                seasonal_windows__month_start__lte=max(month_nums),
                seasonal_windows__month_end__gte=min(month_nums),
                seasonal_windows__rating__in=['best', 'good'],
            ).distinct()

    if min_price:
        qs = qs.filter(price_usd__gte=min_price)
    if max_price:
        qs = qs.filter(price_usd__lte=max_price)

    if q:
        qs = qs.filter(
            _kw_q(q, ['title', 'place_name', 'tags__name',
                      'focus_keyword', 'secondary_keywords'])
        ).distinct()

    # ── Sort ──────────────────────────────────────────────
    sort = request.GET.get('sort', 'popular')
    sort_map = {
        'popular':    '-page_views',
        'price_asc':  'price_usd',
        'price_desc': '-price_usd',
        'duration':   'duration_days',
        'newest':     '-created_at',
        'rating':     '-avg_rating',
    }
    qs = qs.order_by('-is_featured', sort_map.get(sort, '-page_views'))
    return qs


# ── Tour list ─────────────────────────────────────────────
# Shared-host optimization: cache public list pages (content updates via admin are infrequent)
@cache_page(60 * 20)   # 20 minutes
def tour_list(request):
    _save_last_url(request)
    qs          = _tours_queryset(request)
    paginator   = Paginator(qs, 12)
    page_obj    = paginator.get_page(request.GET.get('page', 1))
    categories  = TourCategory.objects.filter(tours__is_active=True).distinct()
    total_count = qs.count()

    # Context for filters
    active_types        = request.GET.getlist('type')
    active_difficulties = request.GET.getlist('difficulty')
    active_duration     = request.GET.get('duration', '')
    active_months       = request.GET.getlist('month')
    active_category     = request.GET.get('category', '')

    MONTHS = [
        {'value': str(i), 'label': m, 'is_best': i in [6, 7, 8, 9, 10]}
        for i, m in enumerate(
            ['Jan','Feb','Mar','Apr','May','Jun',
             'Jul','Aug','Sep','Oct','Nov','Dec'], 1
        )
    ]

    # ── SEO: popular tags (internal-link mesh) + structured data ──
    popular_tags = (
        Tag.objects.annotate(n=Count('tours'))
        .filter(n__gt=0).order_by('-n', 'name')[:14]
    )

    breadcrumb_ld = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home',
             'item': request.build_absolute_uri('/')},
            {'@type': 'ListItem', 'position': 2, 'name': 'Tours',
             'item': request.build_absolute_uri('/tours/')},
        ],
    }
    item_list_ld = {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'name': 'Tanzania Tours & Kilimanjaro Climbs',
        'numberOfItems': total_count,
        'itemListElement': [
            {
                '@type': 'ListItem',
                'position': idx,
                'url': request.build_absolute_uri(t.get_absolute_url()),
                'name': t.title,
            }
            for idx, t in enumerate(page_obj, start=1)
        ],
    }
    json_ld = json.dumps([breadcrumb_ld, item_list_ld])

    return render(request, 'tours/tour_list.html', {
        'tours':               page_obj,
        'page_obj':            page_obj,
        'total_count':         total_count,
        'categories':          categories,
        'active_types':        active_types,
        'active_difficulties': active_difficulties,
        'active_duration':     active_duration,
        'active_months':       active_months,
        'active_category':     active_category,
        'months':              MONTHS,
        'sort':                request.GET.get('sort', 'popular'),
        'tour_types':          Tour.TOUR_TYPE_CHOICES,
        'difficulties':        Tour.DIFFICULTY_CHOICES,
        'page_title':          'All Adventures',
        'duration_ranges': [
            {'value': '1-3',  'label': '1–3 days'},
            {'value': '4-7',  'label': '4–7 days'},
            {'value': '8+',   'label': '8+ days'},
        ],
        # SEO
        'meta_title':       'Tanzania Tours — Kilimanjaro, Safari & More | VISIT KILI ADVNTURES',
        'meta_description': 'Browse all Kilimanjaro treks, Tanzania safaris and day trips. Transparent pricing, live availability.',
        'canonical_url':    request.build_absolute_uri('/tours/'),
        'popular_tags':     popular_tags,
        'json_ld':          json_ld,
    })


# ── Tour detail ───────────────────────────────────────────

def tour_detail(request, slug):
    tour = get_object_or_404(
        Tour.objects.select_related('category', 'itinerary')
                    .prefetch_related(
                        'tags', 'inclusions', 'exclusions',
                        'content_blocks', 'gallery',
                        'seasonal_windows', 'group_departures',
                        'tour_reviews', 'related_guides',
                        'blog_articles',
                    )
                    .only(
                        'title', 'slug', 'excerpt', 'description', 'price_usd',
                        'meta_title', 'meta_description', 'focus_keyword',
                        'duration_days', 'difficulty', 'is_active',
                        'category', 'itinerary', 'page_views',
                    ),
        slug=slug, is_active=True
    )

    # Track view + save session
    Tour.objects.filter(pk=tour.pk).update(page_views=tour.page_views + 1)
    _save_last_url(request)

    # Itinerary items
    itinerary_items = []
    if tour.itinerary:
        itinerary_items = tour.itinerary.items.prefetch_related('tags').order_by('order', 'day_number')

    # Related tours — same tags or category (optimized to avoid loading full tags + distinct overhead on shared host)
    tag_ids = list(tour.tags.values_list('id', flat=True))
    related_tours = Tour.objects.filter(
        Q(tags__in=tag_ids) | Q(category=tour.category),
        is_active=True
    ).exclude(pk=tour.pk).distinct()[:4]

    # Related guides
    related_guides = tour.related_guides.filter(is_published=True)[:4]

    # Reviews
    approved_reviews = tour.tour_reviews.filter(is_approved=True).order_by('-created_at')
    reviews = approved_reviews[:6]

    # Star distribution for the aggregate panel (from real approved reviews)
    rating_distribution = []
    total_r = approved_reviews.count()
    if total_r:
        from collections import Counter
        counts = Counter(approved_reviews.values_list('rating', flat=True))
        for star in (5, 4, 3, 2, 1):
            cnt = counts.get(star, 0)
            rating_distribution.append({
                'star': star,
                'count': cnt,
                'pct': round(cnt / total_r * 100),
            })

    # === CRAZY SEO ENGINE ===
    # Replaces the old minimal schema. Pulls everything the seo-tour skill + import put in:
    # - focus_keyword, meta, secondary
    # - content_blocks faqs
    # - itinerary, reviews, related mesh
    # Multiple schemas for maximum rich results (Product/Offer/FAQ/TouristTrip/Breadcrumb)
    from apps.core.seo_engine import get_tour_schemas
    json_ld = get_tour_schemas(tour, request)

    return render(request, 'tours/tour_detail.html', {
        'tour':             tour,
        'itinerary_items':  itinerary_items,
        'related_tours':    related_tours,
        'related_guides':   related_guides,
        'reviews':          reviews,
        'rating_distribution': rating_distribution,
        'json_ld':          json_ld,   # Now a full HTML block with multiple scripts
        'meta_title':       tour.meta_title or tour.title,
        'meta_description': tour.meta_description or tour.excerpt,
        'canonical_url':    tour.canonical_url or request.build_absolute_uri(tour.get_absolute_url()),
        'og_image':         tour.og_image or tour.feature_image,
    })


# ── Tag page — SEO mesh hub ───────────────────────────────
@cache_page(60 * 15)
def tag_page(request, slug):
    tag           = get_object_or_404(Tag, slug=slug, is_active=True)
    tours         = Tour.objects.filter(tags=tag, is_active=True).prefetch_related('tags', 'seasonal_windows', 'group_departures')
    guides        = tag.trek_guides.filter(is_published=True)
    articles      = tag.blog_articles.filter(status='published')
    related_tags  = Tag.objects.filter(
        topic_pillar=tag.topic_pillar, is_active=True
    ).exclude(pk=tag.pk)[:12]
    all_tags      = Tag.objects.filter(is_active=True).order_by('name')

    _save_last_url(request)

    # BreadcrumbList schema
    schema = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home',  'item': request.build_absolute_uri('/')},
            {'@type': 'ListItem', 'position': 2, 'name': 'Tours', 'item': request.build_absolute_uri('/tours/')},
            {'@type': 'ListItem', 'position': 3, 'name': tag.name,'item': request.build_absolute_uri()},
        ]
    }

    return render(request, 'tours/tag_page.html', {
        'tag':          tag,
        'tours':        tours,
        'guides':       guides,
        'articles':     articles,
        'related_tags': related_tags,
        'all_tags':     all_tags,
        'schema_json':  schema,
        'meta_title':   tag.meta_title or f"{tag.name} Tours & Guides | VISIT KILI ADVNTURES",
        'meta_description': tag.meta_description or f"Browse {tag.name} tours, trek guides and articles.",
        'canonical_url': request.build_absolute_uri(),
    })


# ── Category page ─────────────────────────────────────────

def category_page(request, slug):
    category    = get_object_or_404(TourCategory, slug=slug)
    tours       = Tour.objects.filter(
        category=category, is_active=True
    ).prefetch_related('tags', 'seasonal_windows', 'group_departures', 'inclusions')

    featured    = tours.filter(is_featured=True).first()

    # Rich aggregates for user-friendly content
    stats = tours.aggregate(
        min_price=Min('price_usd'),
        max_price=Max('price_usd'),
        avg_duration=Avg('duration_days'),
        count=Count('id'),
    )
    durations = sorted(set(tours.values_list('duration_days', flat=True)))
    difficulties = list(tours.values_list('difficulty', flat=True))
    from collections import Counter
    diff_counts = Counter(difficulties).most_common(4)  # list of tuples for template for-loop safety

    # Sample top inclusions across category (for highlights)
    top_inclusions = []
    try:
        inc_qs = tours.values('inclusions__name').annotate(c=Count('id')).order_by('-c')[:6]
        top_inclusions = [i['inclusions__name'] for i in inc_qs if i['inclusions__name']]
    except Exception:
        pass

    _save_last_url(request)

    return render(request, 'tours/category_page.html', {
        'category':   category,
        'tours':      tours,
        'featured':   featured,
        'page_title': category.name,
        'meta_title': category.meta_title or f"{category.name} | VISIT KILI ADVNTURES",
        'meta_description': category.meta_description,
        'stats': stats,
        'durations': durations,
        'diff_counts': diff_counts,
        'top_inclusions': top_inclusions,
        'tour_count': stats.get('count', 0),
    })


# ── Category List Hub (for SEO + navigation) ──────────────

@cache_page(60 * 30)
def category_list(request):
    _save_last_url(request)

    # Get all active categories with tour counts and a sample image
    categories = (
        TourCategory.objects.filter(tours__is_active=True)
        .annotate(tour_count=Count('tours', filter=Q(tours__is_active=True)))
        .prefetch_related('tours')
        .order_by('order', 'name')
        .distinct()
    )

    # Enrich with representative image + prepare groups
    enriched = []
    for cat in categories:
        sample_tour = cat.tours.filter(is_active=True).first()
        image_url = None
        if sample_tour and sample_tour.feature_image:
            image_url = sample_tour.feature_image.url

        # Determine group for abstract sections
        name_lower = (cat.name or '').lower()
        slug_lower = (cat.slug or '').lower()
        if any(x in name_lower or x in slug_lower for x in ['kilimanjaro', 'climb', 'trek', 'meru', 'machame', 'lemosho', 'rongai']):
            group = 'kilimanjaro'
        elif any(x in name_lower or x in slug_lower for x in ['safari', 'serengeti', 'ngorongoro', 'tarangire', 'manyara', 'nyerere', 'ruaha']):
            group = 'safari'
        elif any(x in name_lower or x in slug_lower for x in ['day', 'trip', 'excursion', '1 day']):
            group = 'day_trips'
        else:
            group = 'other'

        enriched.append({
            'category': cat,
            'tour_count': cat.tour_count,
            'image_url': image_url,
            'group': group,
            'url': cat.get_absolute_url(),
        })

    # Group for sections
    from itertools import groupby
    from operator import itemgetter

    grouped = {}
    for g, items in groupby(sorted(enriched, key=itemgetter('group')), key=itemgetter('group')):
        grouped[g] = list(items)

    # Order groups nicely
    group_order = ['kilimanjaro', 'safari', 'day_trips', 'other']
    ordered_groups = [(g, grouped.get(g, [])) for g in group_order if grouped.get(g)]

    # SEO
    meta_title = "Explore All Tour Categories | Kilimanjaro, Safaris & Day Trips"
    meta_description = "Browse every type of adventure we offer — Kilimanjaro climbs, Tanzania safaris, and unforgettable day trips. Find the perfect experience for your trip."

    return render(request, 'tours/category_list.html', {
        'categories': enriched,
        'grouped': ordered_groups,
        'total_categories': len(enriched),
        'page_title': 'Tour Categories',
        'meta_title': meta_title,
        'meta_description': meta_description,
        'canonical_url': request.build_absolute_uri(),
    })


# ── Combo package ─────────────────────────────────────────

def combo_list(request):
    combos = ComboPackage.objects.filter(
        is_active=True
    ).prefetch_related('tours', 'tags')
    return render(request, 'tours/combo_list.html', {
        'combos':     combos,
        'page_title': 'Combo Packages',
        'meta_title': 'Tanzania Combo Packages — Kili + Safari + Zanzibar | VISIT KILI ADVNTURES',
    })


def combo_detail(request, slug):
    combo = get_object_or_404(ComboPackage, slug=slug, is_active=True)
    _save_last_url(request)
    return render(request, 'tours/combo_detail.html', {
        'combo':      combo,
        'meta_title': combo.meta_title or combo.title,
        'meta_description': combo.meta_description or combo.excerpt,
    })


# ── HTMX — departure slots (dual: HTMX partial + JSON API) ──

@require_GET
def group_departure_check(request, tour_slug):
    from apps.booking.models import GroupDeparture
    tour        = get_object_or_404(Tour, slug=tour_slug, is_active=True)
    month       = request.GET.get('month')
    qs          = GroupDeparture.objects.filter(
        tour=tour,
        start_date__gte=timezone.now(),
        is_active=True,
    ).order_by('start_date')

    if month:
        try:
            y, m = month.split('-')
            qs = qs.filter(start_date__year=y, start_date__month=m)
        except ValueError:
            pass

    departures = qs[:6]

    if request.headers.get('HX-Request'):
        return TemplateResponse(
            request,
            'tours/partials/departure_list.html',
            {'departures': departures, 'tour': tour}
        )

    data = [
        {
            'id':              d.id,
            'title':           d.title,
            'date':            d.start_date.strftime('%b %d, %Y'),
            'slots_remaining': d.spots_remaining,
            'price':           str(d.price_per_person),
            'status':          'full' if d.spots_remaining == 0
                               else 'limited' if d.spots_remaining < 5
                               else 'available',
            'is_joinable':     d.is_joinable,
            'url':             d.get_absolute_url(),
        }
        for d in departures
    ]
    return JsonResponse({'tour': tour_slug, 'departures': data})


# ── Search ────────────────────────────────────────────────

def search(request):
    """
    Unified Multi-Pillar Search.
    Searches across Tours, Trekking Guides, and Blog Articles.
    """
    from apps.destinations.models import Destination
    from apps.guide.models import BlogArticle, TrekGuide

    q = request.GET.get('q', '').strip()
    tour_results = []
    guide_results = []
    article_results = []
    destination_results = []

    if q:
        # Search Tours — tokenized keyword match (tags act as search keywords),
        # AND for precision with OR fallback so content is always returned.
        tour_results = _kw_filter(
            Tour.objects.filter(is_active=True).select_related('category').only(
                'title', 'slug', 'feature_image', 'duration_days', 'difficulty',
                'price_usd', 'discount_price', 'category'),
            q, ['title', 'place_name', 'excerpt', 'description',
                'focus_keyword', 'secondary_keywords', 'tags__name'])[:8]

        destination_results = _kw_filter(
            Destination.objects.filter(is_active=True).select_related('category').only(
                'name', 'slug', 'feature_image', 'short_description', 'category'),
            q, ['name', 'short_description', 'description',
                'location_name', 'tags__name', 'focus_keyword'])[:8]

        guide_results = _kw_filter(
            TrekGuide.objects.filter(is_published=True),
            q, ['title', 'focus_keyword', 'excerpt', 'tags__name'])[:8]

        article_results = _kw_filter(
            BlogArticle.objects.filter(status='published'),
            q, ['title', 'focus_keyword', 'excerpt', 'tags__name'])[:8]

    total_count = len(tour_results) + len(destination_results) + len(guide_results) + len(article_results)

    context = {
        'query':           q,
        'tours':           tour_results,
        'destinations':    destination_results,
        'guides':          guide_results,
        'articles':        article_results,
        'total_count':     total_count,
        'count':           total_count,
        'meta_title':      f'Search results for "{q}" | VISIT KILI ADVNTURES',
        'meta_description': f'Explore tours, guides, and articles related to {q} on VISIT KILI ADVNTURES.',
    }
    if request.GET.get('format') == 'json':
        return JsonResponse({
            'query': q,
            'count': total_count,
            'tours': [
                {
                    'title': tour.title,
                    'url': tour.get_absolute_url(),
                    'price_usd': str(tour.final_price),
                    'duration_days': tour.duration_days,
                    'difficulty': tour.get_difficulty_display(),
                }
                for tour in tour_results
            ],
            'destinations': [
                {
                    'title': destination.name,
                    'url': destination.get_absolute_url(),
                    'category': destination.category.name if destination.category else '',
                }
                for destination in destination_results
            ],
            'guides': [
                {
                    'title': guide.title,
                    'url': guide.get_absolute_url(),
                    'reading_time': guide.reading_time,
                }
                for guide in guide_results
            ],
            'articles': [
                {
                    'title': article.title,
                    'url': article.get_absolute_url(),
                }
                for article in article_results
            ],
        })
    if request.headers.get('HX-Request'):
        return render(request, 'tours/partials/search_results.html', context)
    return render(request, 'tours/search_results.html', context)

