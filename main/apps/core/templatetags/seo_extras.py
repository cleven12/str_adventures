"""Brand-consistent, Google-safe <title> generation.

Google truncates SERP titles around ~60 characters. To keep the brand name
"VISIT KILI ADVENTURES" (21 chars) visible on every result — so Google
reliably associates it with the site and surfaces it as the Knowledge
Panel / rich-result brand — every page-specific title segment is capped at
39 chars before " | VISIT KILI ADVENTURES" (24 chars incl. separator) is
appended, keeping the combined title within Google's display budget.
"""

import re

from django import template
from django.utils.html import strip_tags

register = template.Library()

BRAND = "VISIT KILI ADVENTURES"
MAX_SEGMENT = 39


@register.filter(name="seo_title")
def seo_title(value):
    text = strip_tags(str(value or "")).strip()

    # Strip any pre-existing brand occurrence (any position/case) so it's
    # never duplicated when this filter appends the canonical brand suffix.
    text = re.sub(re.escape(BRAND), "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\|\s*\|\s*", " | ", text)
    text = text.strip(" |-—")

    if not text:
        return BRAND

    if len(text) > MAX_SEGMENT:
        text = text[:MAX_SEGMENT - 1].rstrip(" |-—").rstrip() + "…"

    return f"{text} | {BRAND}"
