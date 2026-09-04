from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from .models import TrekGuide, BlogArticle, GuideCategory


def _save_last_url(request):
    request.session['last_url'] = request.path


@cache_page(60 * 20)
def guide_list(request):
    _save_last_url(request)
    qs = TrekGuide.objects.filter(is_published=True).select_related('category').prefetch_related('tags', 'related_tours').only('id', 'title', 'slug', 'excerpt', 'focus_keyword', 'category_id', 'publish_date')
    category = request.GET.get('category')
    q = request.GET.get('q', '').strip()
    if category:
        qs = qs.filter(category__slug=category)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(focus_keyword__icontains=q))
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    categories = GuideCategory.objects.filter(guides__is_published=True).distinct()
    return render(request, 'guide/guide_list.html', {
        'guides': page_obj, 'page_obj': page_obj, 'categories': categories,
        'meta_title': 'Trek Guides & Tips | VISIT KILI ADVNTURES',
        'meta_description': 'Expert Kilimanjaro and Tanzania safari guides, packing lists, route tips.',
    })


def guide_detail(request, slug):
    guide = get_object_or_404(
        TrekGuide.objects.select_related('category', 'author', 'primary_tour')
                         .prefetch_related('tags', 'related_tours', 'content_blocks', 'outgoing_links'),
        slug=slug, is_published=True
    )
    TrekGuide.objects.filter(pk=guide.pk).update(view_count=guide.view_count + 1)
    _save_last_url(request)
    related = TrekGuide.objects.filter(
        Q(tags__in=guide.tags.all()) | Q(category=guide.category), is_published=True
    ).exclude(pk=guide.pk).distinct()[:3]
    schema = {
        '@context': 'https://schema.org', '@type': guide.schema_type,
        'headline': guide.title, 'description': guide.get_meta_description(),
        'url': request.build_absolute_uri(guide.get_absolute_url()),
        'datePublished': guide.publish_date.isoformat() if guide.publish_date else '',
        'dateModified': guide.updated_at.isoformat(),
        'author': {'@type': 'Person', 'name': guide.author.get_full_name() if guide.author else 'VISIT KILI ADVNTURES'},
        'publisher': {'@type': 'Organization', 'name': 'VISIT KILI ADVNTURES'},
    }
    return render(request, 'guide/guide_detail.html', {
        'guide': guide, 'related_guides': related, 'schema_json': schema,
        'meta_title': guide.get_meta_title(), 'meta_description': guide.get_meta_description(),
        'canonical_url': guide.canonical_url or request.build_absolute_uri(guide.get_absolute_url()),
        'og_image': guide.og_image or guide.featured_image,
    })


@cache_page(60 * 20)
def article_list(request):
    _save_last_url(request)
    qs = BlogArticle.objects.filter(status='published').select_related('category').prefetch_related('tags').only('id', 'title', 'slug', 'excerpt', 'focus_keyword', 'category_id', 'publish_date', 'author_id')
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'guide/article_list.html', {
        'articles': page_obj, 'page_obj': page_obj,
        'meta_title': 'Travel Guide Articles | VISIT KILI ADVNTURES',
        'meta_description': 'Tanzania travel tips, safari guides, Kilimanjaro route comparisons.',
    })


def article_detail(request, slug):
    article = get_object_or_404(
        BlogArticle.objects.select_related('category', 'author', 'primary_tour')
                           .prefetch_related('tags', 'related_tours', 'related_guides'),
        slug=slug, status='published'
    )
    BlogArticle.objects.filter(pk=article.pk).update(view_count=article.view_count + 1)
    _save_last_url(request)
    schema = {
        '@context': 'https://schema.org', '@type': article.schema_type,
        'headline': article.title, 'description': article.get_meta_description(),
        'url': request.build_absolute_uri(article.get_absolute_url()),
        'datePublished': article.publish_date.isoformat() if article.publish_date else '',
        'dateModified': article.updated_at.isoformat(),
        'author': {'@type': 'Person', 'name': article.author.get_full_name() if article.author else 'VisitKili'},
        'publisher': {'@type': 'Organization', 'name': 'VISIT KILI ADVNTURES'},
    }
    return render(request, 'guide/article_detail.html', {
        'article': article, 'schema_json': schema,
        'meta_title': article.get_meta_title(), 'meta_description': article.get_meta_description(),
        'canonical_url': article.canonical_url or request.build_absolute_uri(article.get_absolute_url()),
        'og_image': article.og_image or article.featured_image,
    })


def category_guides(request, slug):
    category = get_object_or_404(GuideCategory, slug=slug, is_active=True)
    guides = TrekGuide.objects.filter(category=category, is_published=True)
    articles = BlogArticle.objects.filter(category=category, status='published')
    return render(request, 'guide/category.html', {'category': category, 'guides': guides, 'articles': articles})
