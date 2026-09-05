# apps/destinations/admin.py
import json
from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django import forms
from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanSwitchWidget

from apps.core.admin_unfold import MARKDOWN_OVERRIDES, MarkdownWidget
from apps.core.indexing_stub import GoogleIndexingActionMixin
from .models import Destination, DestinationCategory, DestinationGallery, DestinationFAQ

class DestinationJSONImportForm(forms.Form):
    json_file = forms.FileField(label="Select JSON file", widget=UnfoldAdminFileFieldWidget)
    dry_run = forms.BooleanField(
        required=False, initial=True,
        help_text="Preview changes without saving.",
        widget=UnfoldBooleanSwitchWidget,
    )

class DestinationGalleryInline(TabularInline):
    model = DestinationGallery
    extra = 1
    tab = True

class DestinationFAQInline(TabularInline):
    model = DestinationFAQ
    extra = 1
    tab = True

@admin.register(Destination)
class DestinationAdmin(GoogleIndexingActionMixin, ModelAdmin):
    """
    🗻 Admin for destination pages (parks, mountains, regions).
    """
    change_list_template = "admin/json_import_changelist.html"
    formfield_overrides = MARKDOWN_OVERRIDES
    list_display = ('name', 'category', 'is_active', 'is_featured', 'last_indexed_at', 'updated_at')
    list_filter = ('category', 'is_active', 'is_featured', ('last_indexed_at', admin.EmptyFieldListFilter))
    search_fields = ('name', 'description', 'location_name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [DestinationGalleryInline, DestinationFAQInline]
    filter_horizontal = ('related_tours', 'related_guides', 'related_articles', 'tags')
    readonly_fields = ('last_indexed_at',)
    actions = ['ping_google']

    def ping_google(self, request, queryset):
        from apps.core.indexing_stub import ping_google_and_update
        from django.conf import settings
        count = 0
        for destination in queryset.filter(is_active=True):
            url = f"{settings.FRONTEND_URL}{destination.get_absolute_url()}"
            if ping_google_and_update(destination, url):
                count += 1
        messages.success(request, f"Pinged Google for {count} destination(s).")
    ping_google.short_description = "📡 Ping Google Indexing API"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # `description` is a plain TextField (not CKEditor5Field), so it's
        # outside MARKDOWN_OVERRIDES' class-based matching — hook it in by name.
        if db_field.name == 'description':
            kwargs['widget'] = MarkdownWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json), name='destinations_destination_import_json'),
        ]
        return custom_urls + urls

    def import_json(self, request):
        if request.method == 'POST':
            form = DestinationJSONImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    raw = json.load(request.FILES['json_file'])
                    items = raw if isinstance(raw, list) else [raw]
                    count = 0
                    from apps.core.seo_utils import check_import_conflicts
                    for item in items:
                        conflicts = check_import_conflicts(item, model_type='destination')
                        if conflicts.get('has_conflict'):
                            for w in conflicts.get('warnings', [])[:2]:
                                messages.warning(request, f"[keyword conflict] {w}")
                        rel_warnings = self._import_destination(item, form.cleaned_data['dry_run'])
                        for w in rel_warnings[:5]:
                            messages.warning(request, f"[{item.get('slug', item.get('name', '?'))}] {w}")
                        count += 1
                    label = 'previewed' if form.cleaned_data['dry_run'] else 'imported'
                    messages.success(request, f"{count} destination(s) {label}.")
                    return HttpResponseRedirect(reverse('admin:destinations_destination_changelist'))
                except Exception as e:
                    messages.error(request, f"Error: {e}")
        else:
            form = DestinationJSONImportForm()

        return render(request, 'admin/destinations/import_json.html', {
            'form': form,
            'title': 'Import Destinations from JSON',
            'opts': self.model._meta,
        })

    def _import_destination(self, data, dry_run):
        return import_destination_data(data, dry_run)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:destinations_destination_import_json')
        return super().changelist_view(request, extra_context=extra_context)


def import_destination_data(data, dry_run):
    """Import a single destination from a JSON dict. Used by the admin
    upload view and by the `import_content` management command.
    Returns a list of warning strings (e.g. unresolved related-content slugs)."""
    from django.utils.text import slugify

    warnings = []
    slug = data.get('slug') or slugify(data.get('name', ''))
    if not slug:
        raise ValueError("Destination has no 'slug' and no 'name' to generate one from.")

    # Category
    cat_name = data.get('category')
    category = None
    if cat_name:
        category, _ = DestinationCategory.objects.get_or_create(
            name=cat_name,
            defaults={'slug': cat_name.lower().replace(' ', '-')}
        )

    defaults = {
        'name': data.get('name'),
        'category': category,
        'short_description': data.get('short_description', ''),
        'description': data.get('description', ''),
        'location_name': data.get('location_name', ''),
        'altitude': data.get('altitude', ''),
        'best_time_to_visit': data.get('best_time_to_visit', ''),
        'meta_title': (data.get('seo', {}).get('meta_title', '') or '')[:100],
        'meta_description': data.get('seo', {}).get('meta_description', ''),
        'focus_keyword': (data.get('seo', {}).get('focus_keyword', '') or '')[:100],
        'is_active': data.get('is_active', True),
        'is_featured': data.get('is_featured', False),
    }

    from django.db import transaction
    from apps.tours.models import Tour, Tag
    from apps.guide.models import TrekGuide, BlogArticle

    def _resolve(field_label, slugs, queryset):
        """Set an M2M from a slug list; warn about any slug that didn't match."""
        matched = list(queryset.filter(slug__in=slugs))
        matched_slugs = {obj.slug for obj in matched}
        missing = [s for s in slugs if s not in matched_slugs]
        if missing:
            warnings.append(
                f"{field_label}: no match found for slug(s) {', '.join(missing)} "
                f"— check spelling or that the record already exists."
            )
        return matched

    sid = transaction.savepoint()
    try:
        dest, _ = Destination.objects.update_or_create(slug=slug, defaults=defaults)

        if 'related_tours' in data:
            dest.related_tours.set(_resolve('related_tours', data['related_tours'], Tour.objects))
        if 'related_guides' in data:
            dest.related_guides.set(_resolve('related_guides', data['related_guides'], TrekGuide.objects))
        if 'related_articles' in data:
            dest.related_articles.set(_resolve('related_articles', data['related_articles'], BlogArticle.objects))
        if 'tags' in data:
            dest.tags.set(Tag.objects.filter(slug__in=data['tags']))

        # FAQs — replace existing
        faqs = data.get('faqs', [])
        if faqs:
            dest.faqs.all().delete()
            DestinationFAQ.objects.bulk_create([
                DestinationFAQ(
                    destination=dest,
                    question=(faq.get('question', '') or '')[:255],
                    answer=faq.get('answer', ''),
                    order=faq.get('order', i),
                )
                for i, faq in enumerate(faqs)
            ])

        # Gallery — replace existing
        gallery = data.get('gallery', [])
        if gallery:
            dest.gallery.all().delete()
            DestinationGallery.objects.bulk_create([
                DestinationGallery(
                    destination=dest,
                    image=g.get('cloudinary_url', ''),
                    alt_text=(g.get('alt_text', '') or '')[:200],
                    order=g.get('order', i),
                )
                for i, g in enumerate(gallery)
            ])

        if dry_run:
            transaction.savepoint_rollback(sid)
        else:
            transaction.savepoint_commit(sid)
    except Exception:
        transaction.savepoint_rollback(sid)
        raise

    return warnings


@admin.register(DestinationCategory)
class DestinationCategoryAdmin(ModelAdmin):
    """
    🗂️ Admin for destination categories (National Parks, Regions, etc).
    """
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
