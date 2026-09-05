"""
SEO Utilities for Visit Kili.

Includes:
- Keyword conflict detection (for import JSON from skills)
- Duplicate / cannibalization checks for focus_keyword, meta, tags
- Helpers for importers

Shared hosting friendly: uses efficient querysets, no heavy computation.
"""

from django.db.models import Q
from django.utils.text import slugify


def get_active_content_models():
    """Return querysets for content types that can compete on keywords."""
    from apps.tours.models import Tour
    from apps.guide.models import TrekGuide, BlogArticle
    from apps.destinations.models import Destination

    return {
        'tour': Tour.objects.filter(is_active=True),
        'guide': TrekGuide.objects.filter(is_published=True),
        'article': BlogArticle.objects.filter(status='published'),
        'destination': Destination.objects.filter(is_active=True),
    }


def detect_focus_keyword_conflicts(focus_keyword: str, current_slug: str = None, current_type: str = None):
    """
    Find other published/active content using the exact same focus_keyword.
    Used during JSON import dry-runs and pre-save.

    Returns list of conflicts:
    [
        {'type': 'tour', 'slug': '..', 'title': '..', 'url': '..', 'focus_keyword': '..'},
        ...
    ]
    """
    if not focus_keyword or not focus_keyword.strip():
        return []

    conflicts = []
    content = get_active_content_models()

    fk = focus_keyword.strip().lower()

    # Tours
    for t in content['tour'].filter(focus_keyword__iexact=fk):
        if current_slug and current_type == 'tour' and t.slug == current_slug:
            continue
        conflicts.append({
            'type': 'tour',
            'slug': t.slug,
            'title': t.title,
            'focus_keyword': t.focus_keyword,
            'url': f"/tours/{t.slug}/",
        })

    # Guides
    for g in content['guide'].filter(focus_keyword__iexact=fk):
        if current_slug and current_type == 'guide' and g.slug == current_slug:
            continue
        conflicts.append({
            'type': 'guide',
            'slug': g.slug,
            'title': g.title,
            'focus_keyword': g.focus_keyword,
            'url': g.get_absolute_url() if hasattr(g, 'get_absolute_url') else f"/guides/{g.slug}/",
        })

    # Articles
    for a in content['article'].filter(focus_keyword__iexact=fk):
        if current_slug and current_type == 'article' and a.slug == current_slug:
            continue
        conflicts.append({
            'type': 'article',
            'slug': a.slug,
            'title': a.title,
            'focus_keyword': a.focus_keyword,
            'url': a.get_absolute_url() if hasattr(a, 'get_absolute_url') else f"/guides/articles/{a.slug}/",
        })

    # Destinations (they have focus too)
    for d in content['destination'].filter(focus_keyword__iexact=fk):
        if current_slug and current_type == 'destination' and d.slug == current_slug:
            continue
        conflicts.append({
            'type': 'destination',
            'slug': d.slug,
            'title': d.name,
            'focus_keyword': d.focus_keyword,
            'url': d.get_absolute_url() if hasattr(d, 'get_absolute_url') else f"/destinations/{d.slug}/",
        })

    return conflicts


def detect_similar_keyword_conflicts(focus_keyword: str, threshold=0.7):
    """
    Lightweight similarity check for potential cannibalization.
    Simple word overlap. For shared host we avoid heavy libs like fuzzywuzzy unless installed.
    """
    if not focus_keyword:
        return []
    conflicts = []
    fk_words = set(focus_keyword.lower().split())

    content = get_active_content_models()
    all_items = []

    for t in content['tour']:
        if t.focus_keyword:
            all_items.append(('tour', t.slug, t.title, t.focus_keyword))
    for g in content['guide']:
        if g.focus_keyword:
            all_items.append(('guide', g.slug, g.title, g.focus_keyword))
    # Add articles/dests if needed

    for typ, sl, title, other_fk in all_items:
        other_words = set(other_fk.lower().split())
        overlap = len(fk_words & other_words) / max(len(fk_words), 1)
        if overlap >= threshold and other_fk.lower() != focus_keyword.lower():
            conflicts.append({
                'type': typ,
                'slug': sl,
                'title': title,
                'focus_keyword': other_fk,
                'overlap': round(overlap, 2),
            })
    return conflicts[:5]  # limit output


def check_import_conflicts(data: dict, model_type: str = 'tour'):
    """
    Main function called by importers.
    Returns dict with:
    {
        'has_conflict': bool,
        'conflicts': [...],
        'warnings': [...],
        'suggested_focus': 'new-focus-keyword' or None
    }
    """
    seo = data.get('seo', {}) or {}
    focus = seo.get('focus_keyword') or data.get('focus_keyword', '')
    slug = data.get('slug') or ''
    title = data.get('title') or data.get('name', '')

    conflicts = detect_focus_keyword_conflicts(focus, current_slug=slug, current_type=model_type)
    similar = detect_similar_keyword_conflicts(focus) if focus else []

    warnings = []
    has_conflict = bool(conflicts)

    if conflicts:
        warnings.append(f"Focus keyword '{focus}' is already used by {len(conflicts)} other active page(s).")
        for c in conflicts[:3]:
            warnings.append(f"  → {c['type'].title()}: {c['title']} (/{c['slug']})")

    if similar:
        warnings.append("Similar keywords detected (possible cannibalization):")
        for s in similar:
            warnings.append(f"  ~ {s['focus_keyword']} ({s['overlap']*100:.0f}% overlap)")

    # Simple suggestion if conflict
    suggested = None
    if has_conflict and focus:
        base = focus
        for i in range(2, 6):
            candidate = f"{base}-{i}"
            if not detect_focus_keyword_conflicts(candidate):
                suggested = candidate
                break

    return {
        'has_conflict': has_conflict,
        'conflicts': conflicts,
        'similar': similar,
        'warnings': warnings,
        'suggested_focus_keyword': suggested,
    }


def resolve_keyword_conflict(focus_keyword: str, strategy: str = 'warn'):
    """
    Helper for importers.
    strategy: 'warn' | 'skip' | 'rename' | 'proceed'
    Returns (final_focus or None, action_taken)
    """
    if strategy == 'proceed':
        return focus_keyword, 'proceed'

    conflicts = detect_focus_keyword_conflicts(focus_keyword)
    if not conflicts:
        return focus_keyword, 'ok'

    if strategy == 'skip':
        return None, 'skipped'

    if strategy == 'rename':
        suggested = check_import_conflicts({'seo': {'focus_keyword': focus_keyword}}, 'tour')['suggested_focus_keyword']
        return suggested or f"{focus_keyword}-alt", 'renamed'

    return focus_keyword, 'warned'


def bulk_validate_focus_keywords(items: list[dict]) -> list[dict]:
    """
    Run conflict detection across a list of items (for pre-import validation).
    Returns list of problematic items with details.
    This is useful for large batch JSON validation.
    """
    problems = []
    seen_keywords = {}

    for idx, item in enumerate(items):
        seo = item.get("seo", {}) or {}
        fk = (seo.get("focus_keyword") or item.get("focus_keyword", "")).strip().lower()
        if not fk:
            continue

        if fk in seen_keywords:
            problems.append({
                "index": idx,
                "focus_keyword": fk,
                "issue": "duplicate_in_batch",
                "other_index": seen_keywords[fk],
            })
        else:
            seen_keywords[fk] = idx

        external = detect_focus_keyword_conflicts(fk)
        if external:
            problems.append({
                "index": idx,
                "focus_keyword": fk,
                "issue": "conflict_with_live",
                "conflicts": external[:3],
            })

    return problems


def suggest_improved_meta(title: str, focus: str, max_len: int = 60) -> str:
    """Simple helper to suggest better meta titles (used in CLI reports)."""
    if len(title) <= max_len and focus.lower() in title.lower():
        return title
    base = focus.title()
    if len(base) > max_len:
        base = base[:max_len]
    return base + " | Visit Kili" if len(base) < max_len - 12 else base[:max_len]


def count_keyword_usage(focus_keyword: str) -> int:
    """Return how many active content items use this focus keyword. Useful for reports and import validation."""
    if not focus_keyword:
        return 0
    from apps.tours.models import Tour
    from apps.destinations.models import Destination
    from apps.guide.models import TrekGuide, BlogArticle
    fk = focus_keyword.strip()
    count = 0
    count += Tour.objects.filter(is_active=True, focus_keyword__iexact=fk).count()
    count += Destination.objects.filter(is_active=True, focus_keyword__iexact=fk).count()
    count += TrekGuide.objects.filter(is_published=True, focus_keyword__iexact=fk).count()
    count += BlogArticle.objects.filter(status='published', focus_keyword__iexact=fk).count()
    return count


def has_basic_seo_fields(item: dict) -> bool:
    """Check if item dict has the minimum SEO fields populated for import success."""
    seo = item.get("seo") or {}
    return bool(
        seo.get("focus_keyword")
        or item.get("focus_keyword")
    )
