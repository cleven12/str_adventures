# apps/core/context_processors.py — Structured Adventures
import hashlib
from functools import lru_cache
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count
from .models import SiteSettings
from apps.tours.models import TourCategory


@lru_cache(maxsize=1)
def _static_asset_version() -> str:
    candidates = [
        Path(settings.BASE_DIR) / "static" / "dist" / "tailwind.css",
        Path(settings.STATIC_ROOT) / "dist" / "tailwind.css",
    ]
    for path in candidates:
        try:
            if path.is_file() and path.stat().st_size > 0:
                return hashlib.md5(path.read_bytes()).hexdigest()[:12]
        except OSError:
            continue
    return "1"


def site_settings(request):
    currency_options = [
        {'code': 'USD', 'symbol': '$',   'label': 'US Dollar'},
        {'code': 'EUR', 'symbol': '€',   'label': 'Euro'},
        {'code': 'GBP', 'symbol': '£',   'label': 'British Pound'},
        {'code': 'TZS', 'symbol': 'TSh', 'label': 'Tanzanian Shilling'},
    ]
    current_currency = request.session.get('currency', 'USD') if hasattr(request, 'session') else 'USD'
    current_currency_symbol = next(
        (c['symbol'] for c in currency_options if c['code'] == current_currency), '$'
    )
    return {
        'site_settings':           SiteSettings.objects.first(),
        'SITE_NAME':               getattr(settings, 'SITE_NAME', 'Structured Adventures'),
        'SITE_DOMAIN':             getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com'),
        'WHATSAPP_NUMBER':         getattr(settings, 'WHATSAPP_NUMBER', ''),
        'TIKTOK_HANDLE':           getattr(settings, 'TIKTOK_HANDLE', ''),
        'STATIC_ASSET_VERSION':    _static_asset_version(),
        'current_currency':        current_currency,
        'current_currency_symbol': current_currency_symbol,
        'currency_options':        currency_options,
        'currency_symbols':        {'USD': '$', 'EUR': '€', 'GBP': '£', 'TZS': 'TSh'},
    }


def _compute_brand_rating():
    from apps.reviews.models import TourReview, ExternalReview
    ta = TourReview.objects.filter(is_approved=True).aggregate(avg=Avg('rating'), count=Count('id'))
    ea = ExternalReview.objects.filter(is_active=True).aggregate(avg=Avg('rating'), count=Count('id'))
    tc, ec = ta['count'] or 0, ea['count'] or 0
    total = tc + ec
    if not total:
        return None
    weighted = (ta['avg'] or 0) * tc + (ea['avg'] or 0) * ec
    return {'value': round(weighted / total, 1), 'count': total}


def brand_rating(request):
    data = cache.get_or_set('brand_aggregate_rating', _compute_brand_rating, 3600)
    return {
        'BRAND_RATING_VALUE': data['value'] if data else None,
        'BRAND_RATING_COUNT': data['count'] if data else None,
    }


def tour_navigation(request):
    active = (
        TourCategory.objects
        .filter(tours__is_active=True)
        .distinct()
        .order_by('order', 'name')
    )
    kili, safari, daytrip = [], [], []
    for cat in active:
        n = (cat.name or '').lower()
        if any(k in n for k in ['kilimanjaro', 'climb', 'meru', 'machame', 'lemosho', 'rongai', 'marangu', 'northern circuit']):
            kili.append(cat)
        elif any(s in n for s in ['safari', 'serengeti', 'ngorongoro', 'tarangire']):
            safari.append(cat)
        else:
            daytrip.append(cat)
    return {
        'nav_kilimanjaro_categories': kili[:6],
        'nav_safari_categories':      safari[:6],
        'nav_daytrip_categories':     daytrip[:6],
        'nav_all_categories':         list(active)[:12],
    }
