# apps/tours/admin.py

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
    Tag, TourCategory, Inclusion, Exclusion,
    Itinerary, ItineraryItem, Tour, TourImage,
    SeasonalWindow, TourContentBlock, ComboPackage,
    TourAvailability,
)


# ── JSON Import Form ──────────────────────────────────────
class TourJSONImportForm(forms.Form):
    json_file = forms.FileField(
        label="Tour JSON file",
        help_text="Upload a .json file. Existing tours matched by slug will be updated.",
        widget=UnfoldAdminFileFieldWidget,
    )
    dry_run = forms.BooleanField(
        required=False, initial=False,
        label="Dry run",
        help_text="Validate and preview without saving anything.",
        widget=UnfoldBooleanSwitchWidget,
    )
    CONFLICT_CHOICES = [
        ('warn', 'Warn but proceed (recommended)'),
        ('skip', 'Skip items with keyword conflicts'),
        ('rename', 'Auto-rename focus keyword (append -2 etc)'),
        ('proceed', 'Ignore conflicts (force)'),
    ]
    conflict_strategy = forms.ChoiceField(
        choices=CONFLICT_CHOICES,
        initial='warn',
        required=True,
        label="Keyword conflict strategy",
        help_text="What to do when imported focus_keyword already targets another active page.",
        widget=UnfoldAdminRadioSelectWidget,
    )


# ── Tag ───────────────────────────────────────────────────
@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """
    🏷️ Admin for SEO/content tags shared across tours, guides, and articles.
    """
    list_display  = ('name', 'topic_pillar', 'is_active', 'tour_count')
    list_filter   = ('topic_pillar', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)

    def tour_count(self, obj):
        return obj.tours.count()
    tour_count.short_description = '🥾 Tours'


# ── TourCategory ──────────────────────────────────────────
@admin.register(TourCategory)
class TourCategoryAdmin(ModelAdmin):
    """
    🗂️ Admin for tour categories (Kilimanjaro, Safari, Zanzibar, etc).
    """
    list_display  = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering      = ('order',)


# ── Inclusion / Exclusion ─────────────────────────────────
@admin.register(Inclusion)
class InclusionAdmin(ModelAdmin):
    """✅ What's included in a tour package."""
    list_display  = ('name', 'icon')
    search_fields = ('name',)

@admin.register(Exclusion)
class ExclusionAdmin(ModelAdmin):
    """🚫 What's excluded from a tour package."""
    list_display  = ('name',)
    search_fields = ('name',)


# ── Itinerary ─────────────────────────────────────────────
class ItineraryItemInline(TabularInline):
    model   = ItineraryItem
    extra   = 1
    fields  = ('day_number', 'time', 'title', 'description', 'tags', 'order')
    ordering = ('order', 'day_number')
    filter_horizontal = ('tags',)
    tab = True

@admin.register(Itinerary)
class ItineraryAdmin(ModelAdmin):
    """
    🗺️ Admin for reusable day-by-day itineraries attached to tours.
    """
    list_display  = ('name', 'slug', 'item_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    inlines       = [ItineraryItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = '📅 Days'


# ── TourImage inline ──────────────────────────────────────
class TourImageInline(TabularInline):
    model   = TourImage
    extra   = 2
    fields  = ('image', 'alt_text', 'caption', 'order', 'is_hero')
    ordering = ('order',)
    tab = True


# ── SeasonalWindow inline ─────────────────────────────────
class SeasonalWindowInline(TabularInline):
    model   = SeasonalWindow
    extra   = 1
    fields  = ('month_start', 'month_end', 'rating', 'notes')
    tab = True


# ── TourContentBlock inline ───────────────────────────────
class TourContentBlockInline(StackedInline):
    model   = TourContentBlock
    extra   = 0
    fields  = ('block_type', 'heading', 'content', 'order', 'include_in_toc', 'focus_keyword')
    ordering = ('order',)
    formfield_overrides = MARKDOWN_OVERRIDES
    tab = True


# ── Tour ──────────────────────────────────────────────────
@admin.register(Tour)
class TourAdmin(GoogleIndexingActionMixin, ModelAdmin):
    """
    🥾 Admin for tours & treks — the core bookable product.
    """
    change_list_template = "admin/json_import_changelist.html"
    formfield_overrides = MARKDOWN_OVERRIDES
    list_display  = (
        'title', 'tour_type', 'category', 'price_usd',
        'duration_days', 'is_active', 'is_featured',
        'last_indexed_at'
    )
    list_filter   = (
        'tour_type', 'difficulty', 'is_active', 'is_featured', 'category',
        ('last_indexed_at', admin.EmptyFieldListFilter),
    )
    search_fields = ('title', 'slug', 'focus_keyword', 'place_name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_active', 'is_featured')
    filter_horizontal = ('tags', 'inclusions', 'exclusions')
    raw_id_fields = ('itinerary', 'category')
    readonly_fields = ('page_views', 'last_indexed_at', 'created_at', 'updated_at')
    inlines = [TourImageInline, SeasonalWindowInline, TourContentBlockInline]

    fieldsets = (
        ('🥾 Core', {
            'fields': (
                'title', 'slug', 'category', 'tour_type',
                'place_name', 'tags', 'itinerary',
            )
        }),
        ('📝 Content', {
            'fields': ('description', 'excerpt')
        }),
        ('📋 Details', {
            'fields': (
                'duration_days', 'difficulty', 'group_size',
                'max_altitude', 'target_audience',
                'lodge_level', 'beach_type',
            )
        }),
        ('💰 Pricing', {
            'fields': ('price_usd', 'discount_price', 'deposit_percentage')
        }),
        ('✅ Inclusions / 🚫 Exclusions', {
            'fields': ('inclusions', 'exclusions'),
            'classes': ('collapse',)
        }),
        ('🖼️ Media', {
            'fields': ('feature_image', 'image_alt_text', 'og_image')
        }),
        ('🔍 SEO', {
            'fields': (
                'meta_title', 'meta_description', 'focus_keyword', 'secondary_keywords',
                'canonical_url', 'og_title', 'og_description',
                'twitter_card_type', 'schema_type', 'seo_priority',
                'structured_data',
            ),
            'classes': ('collapse',)
        }),
        ('🚦 Status', {
            'fields': (
                'is_active', 'is_featured',
                'page_views', 'last_indexed_at',
                'created_at', 'updated_at',
            )
        }),
    )

    # ── JSON import via custom admin view ─────────────────
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'import-json/',
                self.admin_site.admin_view(self.import_json_view),
                name='tours_tour_import_json'
            )
        ]
        return custom + urls

    def import_json_view(self, request):
        if request.method == 'POST':
            form = TourJSONImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    raw = json.load(request.FILES['json_file'])
                    # Support both single object and list
                    items = raw if isinstance(raw, list) else [raw]
                    from apps.tours.services.tour_import_service import TourImportService
                    results = []
                    conflict_strategy = form.cleaned_data.get('conflict_strategy', 'warn') if hasattr(form, 'cleaned_data') else 'warn'

                    for item in items:
                        result = TourImportService.import_from_dict(
                            item,
                            dry_run=form.cleaned_data['dry_run'],
                            conflict_strategy=conflict_strategy,
                        )
                        results.append(result)

                    ok = [r for r in results if r.get('status') in ('ok', 'skipped')]
                    err = [r for r in results if r.get('status') == 'error']
                    skipped = [r for r in results if r.get('status') == 'skipped']
                    conflicted = [r for r in results if r.get('has_keyword_conflict') or r.get('conflicts', {}).get('has_conflict')]

                    if err:
                        messages.warning(request, f"{len(ok)} processed, {len(err)} failed.")
                    elif skipped:
                        messages.warning(request, f"{len(ok)} processed, {len(skipped)} skipped due to keyword conflicts.")
                    elif conflicted:
                        messages.warning(request, f"{len(ok)} imported/previewed. {len(conflicted)} had keyword conflicts (see details).")
                    else:
                        label = 'previewed' if form.cleaned_data['dry_run'] else 'imported'
                        messages.success(request, f"{len(ok)} tour(s) {label} successfully.")

                    # Show specific conflict warnings from first few
                    for r in results[:5]:
                        for w in r.get('warnings', [])[:2]:
                            messages.info(request, f"[{r.get('slug','')}] {w}")
                    return HttpResponseRedirect(
                        reverse('admin:tours_tour_changelist')
                    )
                except json.JSONDecodeError as e:
                    messages.error(request, f"Invalid JSON: {e}")
                except Exception as e:
                    messages.error(request, f"Import error: {e}")
        else:
            form = TourJSONImportForm()

        return render(request, 'admin/tours/import_json.html', {
            'form': form,
            'title': 'Import Tours from JSON',
            'opts': self.model._meta,
        })

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:tours_tour_import_json')
        return super().changelist_view(request, extra_context=extra_context)

    def ping_google(self, request, queryset):
        from apps.core.indexing_stub import ping_google_and_update
        from django.conf import settings
        count = 0
        for tour in queryset.filter(is_active=True):
            url = f"https://{settings.SITE_DOMAIN}{tour.get_absolute_url()}"
            if ping_google_and_update(tour, url):
                count += 1
        messages.success(request, f"Pinged Google for {count} tour(s).")
    ping_google.short_description = "📡 Ping Google Indexing API"
    actions = ['ping_google']


# ── TourAvailability ──────────────────────────────────────
@admin.register(TourAvailability)
class TourAvailabilityAdmin(ModelAdmin):
    """
    📅 Admin for tour availability windows / capacity per date range.
    """
    status_pill = status_badge('status', description='🚦 Status')
    list_display  = ('tour', 'start_date', 'end_date', 'capacity', 'booked_count', 'status_pill')
    list_filter   = ('status', 'tour')
    search_fields = ('tour__title',)
    raw_id_fields = ('tour',)


# ── ComboPackage ──────────────────────────────────────────
@admin.register(ComboPackage)
class ComboPackageAdmin(GoogleIndexingActionMixin, ModelAdmin):
    """
    🎒 Admin for combo packages bundling multiple tours together.
    """
    formfield_overrides = MARKDOWN_OVERRIDES
    list_display  = ('title', 'total_price', 'duration_days', 'is_active', 'last_indexed_at')
    list_filter   = ('is_active', ('last_indexed_at', admin.EmptyFieldListFilter))
    search_fields = ('title', 'focus_keyword')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tours', 'tags')
    list_editable = ('is_active',)
    readonly_fields = ('last_indexed_at',)

    def ping_google(self, request, queryset):
        from apps.core.indexing_stub import ping_google_and_update
        from django.conf import settings
        count = 0
        for combo in queryset.filter(is_active=True):
            url = f"https://{settings.SITE_DOMAIN}{combo.get_absolute_url()}"
            if ping_google_and_update(combo, url):
                count += 1
        messages.success(request, f"Pinged Google for {count} combo package(s).")
    ping_google.short_description = "📡 Ping Google Indexing API"
    actions = ['ping_google']
