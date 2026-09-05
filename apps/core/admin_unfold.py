"""Shared Django Unfold admin theming helpers.

- MARKDOWN_OVERRIDES: drop into any ModelAdmin's `formfield_overrides` to swap
  django_ckeditor_5.CKEditor5Field to a markdown-native editor (EasyMDE) in
  the admin, with zero model/migration changes (CKEditor5Field is still a
  plain TextField under the hood — content authored as markdown, tables
  included, via EasyMDE's own table toolbar button or raw `| a | b |` syntax).
  Any HTML already saved from the old CKEditor5 WYSIWYG still round-trips
  fine — markdown renderers pass unrecognized raw HTML straight through.
- status_badge(): builds a colored pill for any choice/boolean field, for use
  as a `list_display` entry. Colors are picked by keyword match, no per-model
  color maps to maintain.
"""
from django import forms
from django.conf import settings
from django.utils.html import format_html
from django_ckeditor_5.fields import CKEditor5Field


class MarkdownWidget(forms.Textarea):
    """Plain Textarea storing raw markdown, upgraded client-side to EasyMDE
    (CDN, no build step, no extra pip package). Ships with a table toolbar
    button plus raw `| col | col |` typing, live preview, and fullscreen.
    """

    template_name = "django/forms/widgets/textarea.html"

    class Media:
        css = {
            "all": (
                "https://unpkg.com/easymde/dist/easymde.min.css",
            )
        }
        js = (
            "https://unpkg.com/easymde/dist/easymde.min.js",
            "admin/js/markdown_widget_init.js",
        )

    def __init__(self, attrs=None):
        default_attrs = {"class": "markdown-editor", "rows": 18}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


MARKDOWN_OVERRIDES = {
    CKEditor5Field: {"widget": MarkdownWidget},
}

_BADGE_COLORS = {
    # keyword -> (bg, fg) — matched against the lowercased field value
    "active": ("#dcfce7", "#166534"),
    "published": ("#dcfce7", "#166534"),
    "approved": ("#dcfce7", "#166534"),
    "confirmed": ("#dcfce7", "#166534"),
    "success": ("#dcfce7", "#166534"),
    "paid": ("#dcfce7", "#166534"),
    "completed": ("#dcfce7", "#166534"),
    "draft": ("#fef9c3", "#854d0e"),
    "pending": ("#fef9c3", "#854d0e"),
    "warning": ("#fef9c3", "#854d0e"),
    "review": ("#fef9c3", "#854d0e"),
    "inactive": ("#fee2e2", "#991b1b"),
    "cancelled": ("#fee2e2", "#991b1b"),
    "canceled": ("#fee2e2", "#991b1b"),
    "rejected": ("#fee2e2", "#991b1b"),
    "failed": ("#fee2e2", "#991b1b"),
    "danger": ("#fee2e2", "#991b1b"),
    "expired": ("#fee2e2", "#991b1b"),
}
_DEFAULT_BADGE = ("#e0e7ff", "#3730a3")  # info / anything unmatched


def _colors_for(value: str):
    v = (value or "").lower()
    for keyword, colors in _BADGE_COLORS.items():
        if keyword in v:
            return colors
    return _DEFAULT_BADGE


def status_badge(field_name: str, description: str = "Status"):
    """Return a `list_display`-ready callable that renders `field_name` as a
    colored pill. Usage on a ModelAdmin:

        status_pill = status_badge('status', description='🚦 Status')
        list_display = ('title', 'status_pill', ...)
    """

    def _renderer(self, obj):
        raw = getattr(obj, field_name)
        display_fn = getattr(obj, f"get_{field_name}_display", None)
        label = display_fn() if callable(display_fn) else raw
        bg, fg = _colors_for(str(raw))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:999px;font-size:12px;font-weight:600;'
            'white-space:nowrap;">{}</span>',
            bg, fg, label,
        )

    _renderer.short_description = description
    _renderer.admin_order_field = field_name
    return _renderer


def environment_callback(request):
    """Small colored banner in the Unfold navbar showing DEBUG on/off."""
    if settings.DEBUG:
        return ["DEVELOPMENT", "warning"]
    return ["LIVE", "success"]
