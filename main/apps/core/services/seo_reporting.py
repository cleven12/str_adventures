"""
SEO Reporting service.
Central place for generating reports that can be used in admin, CLI, and future dashboards.

Future commits can expand this heavily (charts data, PDF export, email reports, etc.).
"""

from django.db.models import Count, Q, Avg


def get_tour_seo_summary():
    from apps.tours.models import Tour

    qs = Tour.objects.filter(is_active=True)
    total = qs.count()

    return {
        "total_active": total,
        "with_focus_keyword": qs.exclude(focus_keyword="").count(),
        "complete_seo": qs.filter(
            ~Q(focus_keyword=""),
            ~Q(meta_title=""),
            ~Q(meta_description=""),
        ).count(),
        "avg_price": float(qs.aggregate(avg=Avg('price_usd'))['avg'] or 0),
        "with_complete_seo": qs.filter(focus_keyword__isnull=False, meta_title__isnull=False).count(),  # additional stat
    }


def get_destination_seo_summary():
    from apps.destinations.models import Destination
    qs = Destination.objects.filter(is_active=True)
    return {
        "total_active": qs.count(),
        "with_focus": qs.exclude(focus_keyword="").count(),
    }
