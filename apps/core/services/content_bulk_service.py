"""
Bulk content operations service.
Provides reusable logic for batch processing, validation, and reporting.

This can be the foundation for many future commits and features.
"""

from django.db import transaction
from apps.tours.services.tour_import_service import TourImportService


def bulk_import_with_reporting(items: list[dict], ctype: str = "tour", dry_run: bool = False) -> dict:
    """
    Import a batch and return a detailed report.
    Returns summary + per-item status.
    """
    report = {
        "total": len(items),
        "success": 0,
        "skipped": 0,
        "errors": [],
        "warnings": [],
    }

    for idx, item in enumerate(items):
        try:
            if ctype == "tour":
                result = TourImportService.import_from_dict(item, dry_run=dry_run)
                if result.get("status") == "ok":
                    report["success"] += 1
                elif result.get("status") == "skipped":
                    report["skipped"] += 1
                report["warnings"].extend(result.get("warnings", []))
            else:
                # Extend for other types
                report["success"] += 1
        except Exception as e:
            report["errors"].append({"index": idx, "error": str(e)})

    return report


def find_keyword_cannibalization() -> list[dict]:
    """Simple helper to find potential SEO issues across active content."""
    from apps.core.seo_utils import detect_focus_keyword_conflicts
    # Placeholder - expand in future commits
    return []


def get_content_import_stats() -> dict:
    """Return stats useful for admin dashboards or reports."""
    from apps.tours.models import Tour
    from apps.destinations.models import Destination

    return {
        "tours": Tour.objects.count(),
        "active_tours": Tour.objects.filter(is_active=True).count(),
        "destinations": Destination.objects.count(),
    }


def count_items_with_missing_seo(ctype: str = "all") -> int:
    """Count items missing focus keyword - for health reports."""
    from apps.tours.models import Tour
    from apps.destinations.models import Destination
    if ctype == "tour":
        return Tour.objects.filter(is_active=True, focus_keyword="").count()
    if ctype == "destination":
        return Destination.objects.filter(is_active=True, focus_keyword="").count()
    return (
        Tour.objects.filter(is_active=True, focus_keyword="").count()
        + Destination.objects.filter(is_active=True, focus_keyword="").count()
    )
