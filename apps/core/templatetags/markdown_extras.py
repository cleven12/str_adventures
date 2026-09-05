"""Renders markdown-sourced admin content (guide/tour/FAQ fields) as HTML on
the public site. Raw HTML already saved from the old CKEditor5 editor still
round-trips fine — markdown's default parser passes unrecognized HTML blocks
straight through untouched.
"""
import bleach
import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_ALLOWED_TAGS = [
    "p", "br", "hr", "strong", "em", "b", "i", "u", "s", "del",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a", "img",
    "blockquote", "pre", "code",
    "table", "thead", "tbody", "tr", "th", "td",
    "div", "span",
]
_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "*": ["class"],
}

_MD_EXTENSIONS = [
    "tables",
    "fenced_code",
    "nl2br",
    "sane_lists",
    "toc",
]


@register.filter(name="markdownify", is_safe=True)
def markdownify(text):
    """Convert a markdown (or legacy raw-HTML) field value to safe HTML.

    Usage in a template:  {{ tour.description|markdownify }}
    """
    if not text:
        return ""
    html = md.markdown(text, extensions=_MD_EXTENSIONS)
    clean = bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
    )
    return mark_safe(clean)
