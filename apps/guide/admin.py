# apps/guide/admin.py

import json
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.contrib import messages
from django.shortcuts import render
from django import forms
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanSwitchWidget, UnfoldAdminRadioSelectWidget

from apps.core.admin_unfold import MARKDOWN_OVERRIDES, status_badge
from apps.core.indexing_stub import GoogleIndexingActionMixin
from .models import (
    GuideCategory, TrekGuide, BlogArticle,
    GuideContentBlock, GuideInternalLink
)


# ── Import form ───────────────────────────────────────────
class GuideJSONImportForm(forms.Form):
    json_file = forms.FileField(label="JSON file", widget=UnfoldAdminFileFieldWidget)
    content_type = forms.ChoiceField(
        choices=[('guide', 'Trek Guide'), ('article', 'Blog Article')],
        label="Content type",
        widget=UnfoldAdminRadioSelectWidget,
    )
    dry_run = forms.BooleanField(required=False, label="Dry run", widget=UnfoldBooleanSwitchWidget)


# ── GuideCategory ─────────────────────────────────────────
@admin.register(GuideCategory)
class GuideCategoryAdmin(ModelAdmin):
    """🗂️ Admin for guide/blog categories."""
    list_display  = ('name', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')


# ── GuideContentBlock inline ──────────────────────────────
class GuideContentBlockInline(StackedInline):
    model   = GuideContentBlock
    extra   = 0
    fields  = ('block_type', 'heading', 'content', 'order', 'include_in_toc', 'focus_keyword', 'icon')
    ordering = ('order',)
    formfield_overrides = MARKDOWN_OVERRIDES
    tab = True


# ── GuideInternalLink inline ──────────────────────────────
class GuideInternalLinkInline(TabularInline):
    model   = GuideInternalLink
    extra   = 1
    fk_name = 'from_guide'
    fields  = ('anchor_text', 'link_type', 'to_guide', 'to_tour', 'to_url', 'is_nofollow', 'is_active')
    raw_id_fields = ('to_guide', 'to_tour')
    tab = True


# ── TrekGuide ─────────────────────────────────────────────
@admin.register(TrekGuide)
class TrekGuideAdmin(GoogleIndexingActionMixin, ModelAdmin):
    """
    🧭 Admin for long-form trek guides.
    """
    change_list_template = "admin/json_import_changelist.html"
    formfield_overrides = MARKDOWN_OVERRIDES
    list_display  = (
        'title', 'category', 'difficulty', 'is_published',
        'is_featured', 'view_count', 'reading_time', 'last_indexed_at'
    )
    list_filter   = (
        'is_published', 'is_featured', 'difficulty', 'category',
        ('last_indexed_at', admin.EmptyFieldListFilter),
    )
    search_fields = ('title', 'slug', 'focus_keyword')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published', 'is_featured')
    filter_horizontal = ('tags', 'related_tours')
    raw_id_fields = ('category', 'author', 'primary_tour')
    readonly_fields = ('view_count', 'reading_time', 'last_indexed_at', 'created_at', 'updated_at')
    inlines = [GuideContentBlockInline, GuideInternalLinkInline]

    fieldsets = (
        ('🧭 Core', {
            'fields': ('title', 'slug', 'category', 'author', 'difficulty', 'featured_image', 'image_alt_text')
        }),
        ('📝 Content', {
            'fields': ('first_paragraph', 'excerpt', 'content')
        }),
        ('🔗 Mesh Relations', {
            'fields': ('tags', 'related_tours', 'primary_tour'),
            'description': 'These fields build the SEO mesh — shared tags link this guide to tour pages.'
        }),
        ('🔍 SEO', {
            'fields': (
                'meta_title', 'meta_description', 'focus_keyword',
                'secondary_keywords', 'canonical_url', 'schema_type',
                'og_title', 'og_description', 'og_image'
            ),
            'classes': ('collapse',)
        }),
        ('📣 Publishing', {
            'fields': ('is_published', 'is_featured', 'publish_date')
        }),
        ('📊 Stats', {
            'fields': ('view_count', 'reading_time', 'last_indexed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'import-json/',
                self.admin_site.admin_view(self.import_json_view),
                name='guide_trekguide_import_json'
            )
        ]
        return custom + urls

    def import_json_view(self, request):
        if request.method == 'POST':
            form = GuideJSONImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    raw = json.load(request.FILES['json_file'])
                    items = raw if isinstance(raw, list) else [raw]
                    count = 0
                    content_type = form.cleaned_data['content_type']
                    from apps.core.seo_utils import check_import_conflicts
                    for item in items:
                        ctype = 'article' if content_type == 'article' else 'guide'
                        conflicts = check_import_conflicts(item, model_type=ctype)
                        if conflicts.get('has_conflict'):
                            for w in conflicts.get('warnings', [])[:2]:
                                messages.warning(request, f"[conflict preview] {w}")

                        if content_type == 'article':
                            rel_warnings = _import_article(item, form.cleaned_data['dry_run'])
                        else:
                            rel_warnings = _import_guide(item, form.cleaned_data['dry_run'])
                        for w in rel_warnings[:5]:
                            messages.warning(request, f"[{item.get('slug', item.get('title', '?'))}] {w}")
                        count += 1
                    label = 'previewed' if form.cleaned_data['dry_run'] else 'imported'
                    messages.success(request, f"{count} {content_type}(s) {label}.")
                    return HttpResponseRedirect(reverse('admin:guide_trekguide_changelist'))
                except Exception as e:
                    messages.error(request, f"Error: {e}")
        else:
            form = GuideJSONImportForm()
        return render(request, 'admin/guide/import_json.html', {
            'form': form, 'title': 'Import Guide from JSON', 'opts': self.model._meta
        })

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:guide_trekguide_import_json')
        return super().changelist_view(request, extra_context=extra_context)

    def ping_google(self, request, queryset):
        from apps.core.indexing_stub import ping_google_and_update
        from django.conf import settings
        count = 0
        for guide in queryset.filter(is_published=True):
            url = f"https://{settings.SITE_DOMAIN}{guide.get_absolute_url()}"
            if ping_google_and_update(guide, url):
                count += 1
        messages.success(request, f"Pinged Google for {count} guide(s).")
    ping_google.short_description = "📡 Ping Google Indexing API"
    actions = ['ping_google']


# ── BlogArticle ───────────────────────────────────────────
@admin.register(BlogArticle)
class BlogArticleAdmin(GoogleIndexingActionMixin, ModelAdmin):
    """
    📝 Admin for blog articles.
    """
    formfield_overrides = MARKDOWN_OVERRIDES
    status_pill = status_badge('status', description='🚦 Status')
    list_display  = (
        'title', 'category', 'status_pill', 'publish_date',
        'view_count', 'reading_time', 'last_indexed_at'
    )
    list_filter   = ('status', 'category', ('last_indexed_at', admin.EmptyFieldListFilter))
    search_fields = ('title', 'slug', 'focus_keyword')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags', 'related_tours', 'related_guides')
    raw_id_fields = ('category', 'author', 'primary_tour')
    readonly_fields = ('view_count', 'reading_time', 'last_indexed_at', 'created_at', 'updated_at')

    fieldsets = (
        ('📝 Core', {
            'fields': ('title', 'slug', 'category', 'author', 'featured_image', 'image_alt_text')
        }),
        ('📄 Content', {
            'fields': ('first_paragraph', 'excerpt', 'content')
        }),
        ('🔗 Mesh Relations', {
            'fields': ('tags', 'related_tours', 'primary_tour', 'related_guides'),
        }),
        ('🔍 SEO', {
            'fields': (
                'meta_title', 'meta_description', 'focus_keyword',
                'secondary_keywords', 'canonical_url', 'schema_type',
                'og_title', 'og_description', 'og_image'
            ),
            'classes': ('collapse',)
        }),
        ('📣 Publishing', {
            'fields': ('status', 'publish_date')
        }),
    )

    def ping_google(self, request, queryset):
        from apps.core.indexing_stub import ping_google_and_update
        from django.conf import settings
        count = 0
        for article in queryset.filter(status='published'):
            url = f"https://{settings.SITE_DOMAIN}{article.get_absolute_url()}"
            if ping_google_and_update(article, url):
                count += 1
        messages.success(request, f"Pinged Google for {count} article(s).")
    ping_google.short_description = "📡 Ping Google Indexing API"
    actions = ['ping_google']


def _import_guide(data: dict, dry_run: bool):
    """Import a single guide or blog article from a JSON dict.
    Returns a list of warning strings (e.g. unresolved related-content slugs)."""
    from django.db import transaction
    from django.utils.text import slugify
    from apps.tours.models import Tag, Tour

    warnings = []
    sid = transaction.savepoint()
    try:
        cat_name = data.get('category', 'General')
        category, _ = GuideCategory.objects.get_or_create(name=cat_name)

        slug = data.get('slug') or slugify(data.get('title', ''))
        seo  = data.get('seo', {})

        fields = {
            'title':              data.get('title', ''),
            'category':           category,
            'first_paragraph':    data.get('first_paragraph', ''),
            'excerpt':            (data.get('excerpt') or '')[:300],
            'content':            data.get('content', ''),
            'difficulty':         data.get('difficulty', 'all_levels'),
            'meta_title':         (seo.get('meta_title') or '')[:60],
            'meta_description':   (seo.get('meta_description') or '')[:155],
            'focus_keyword':      (seo.get('focus_keyword') or '')[:100],
            'secondary_keywords': (seo.get('secondary_keywords') or '')[:300],
            'og_title':           (seo.get('og_title') or '')[:95],
            'og_description':     (seo.get('og_description') or '')[:200],
            'schema_type':        seo.get('schema_type', 'Article'),
            'is_published':       data.get('is_published', False),
        }

        guide, _ = TrekGuide.objects.update_or_create(slug=slug, defaults=fields)

        # Tags — created automatically, so no mismatch risk here
        for tag_slug in data.get('tags', []):
            t, _ = Tag.objects.get_or_create(
                slug=slugify(tag_slug),
                defaults={'name': tag_slug.replace('-', ' ').title()}
            )
            guide.tags.add(t)

        # Related tours by slug — Tour is NOT auto-created, so warn on any miss
        related_slugs = data.get('related_tours', [])
        if related_slugs:
            matched = Tour.objects.filter(slug__in=related_slugs)
            matched_slugs = {t.slug for t in matched}
            missing = [s for s in related_slugs if s not in matched_slugs]
            if missing:
                warnings.append(
                    f"related_tours: no match found for slug(s) {', '.join(missing)}"
                )
            guide.related_tours.set(matched)

        # Primary tour by slug
        primary_slug = data.get('primary_tour')
        if primary_slug:
            primary = Tour.objects.filter(slug=primary_slug).first()
            if primary:
                guide.primary_tour = primary
                guide.save(update_fields=['primary_tour'])
            else:
                warnings.append(f"primary_tour: no match found for slug '{primary_slug}'")

        # Content blocks
        blocks = data.get('content_blocks', [])
        if blocks:
            guide.content_blocks.all().delete()
            GuideContentBlock.objects.bulk_create([
                GuideContentBlock(
                    guide=guide,
                    block_type=b.get('type', 'paragraph'),
                    heading=b.get('heading', ''),
                    content=b.get('content', ''),
                    order=b.get('order', i),
                    include_in_toc=b.get('include_in_toc', True),
                    focus_keyword=b.get('focus_keyword', ''),
                    anchor_id=b.get('anchor_id', ''),
                )
                for i, b in enumerate(blocks)
            ])

        if dry_run:
            transaction.savepoint_rollback(sid)
        else:
            transaction.savepoint_commit(sid)
    except Exception:
        transaction.savepoint_rollback(sid)
        raise

    return warnings


def _import_article(data: dict, dry_run: bool):
    """Import a single BlogArticle from a JSON dict.
    Returns a list of warning strings (e.g. unresolved related-content slugs)."""
    from django.db import transaction
    from django.utils.text import slugify
    from apps.tours.models import Tag, Tour

    warnings = []
    sid = transaction.savepoint()
    try:
        cat_name = data.get('category', 'General')
        category, _ = GuideCategory.objects.get_or_create(name=cat_name)

        slug = data.get('slug') or slugify(data.get('title', ''))
        seo  = data.get('seo', {})

        fields = {
            'title':              data.get('title', ''),
            'category':           category,
            'first_paragraph':    data.get('first_paragraph', ''),
            'excerpt':            (data.get('excerpt') or '')[:300],
            'content':            data.get('content', ''),
            'meta_title':         (seo.get('meta_title') or '')[:60],
            'meta_description':   (seo.get('meta_description') or '')[:155],
            'focus_keyword':      (seo.get('focus_keyword') or '')[:100],
            'secondary_keywords': (seo.get('secondary_keywords') or '')[:300],
            'og_title':           (seo.get('og_title') or '')[:95],
            'og_description':     (seo.get('og_description') or '')[:200],
            'schema_type':        seo.get('schema_type', 'BlogPosting'),
            'status':             data.get('status', 'draft'),
        }

        article, _ = BlogArticle.objects.update_or_create(slug=slug, defaults=fields)

        for tag_slug in data.get('tags', []):
            t, _ = Tag.objects.get_or_create(
                slug=slugify(tag_slug),
                defaults={'name': tag_slug.replace('-', ' ').title()}
            )
            article.tags.add(t)

        related_slugs = data.get('related_tours', [])
        if related_slugs:
            matched = Tour.objects.filter(slug__in=related_slugs)
            matched_slugs = {t.slug for t in matched}
            missing = [s for s in related_slugs if s not in matched_slugs]
            if missing:
                warnings.append(f"related_tours: no match found for slug(s) {', '.join(missing)}")
            article.related_tours.set(matched)

        related_guide_slugs = data.get('related_guides', [])
        if related_guide_slugs:
            matched_g = TrekGuide.objects.filter(slug__in=related_guide_slugs)
            matched_g_slugs = {g.slug for g in matched_g}
            missing_g = [s for s in related_guide_slugs if s not in matched_g_slugs]
            if missing_g:
                warnings.append(f"related_guides: no match found for slug(s) {', '.join(missing_g)}")
            article.related_guides.set(matched_g)

        primary_slug = data.get('primary_tour')
        if primary_slug:
            primary = Tour.objects.filter(slug=primary_slug).first()
            if primary:
                article.primary_tour = primary
                article.save(update_fields=['primary_tour'])
            else:
                warnings.append(f"primary_tour: no match found for slug '{primary_slug}'")

        if dry_run:
            transaction.savepoint_rollback(sid)
        else:
            transaction.savepoint_commit(sid)
    except Exception:
        transaction.savepoint_rollback(sid)
        raise

    return warnings
