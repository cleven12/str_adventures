"""
Generate a quick SEO health report for content in the database.

Usage:
    python manage.py seo_report
    python manage.py seo_report --type tour --limit 20
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q


class Command(BaseCommand):
    help = "Quick SEO health report across content types."

    def add_arguments(self, parser):
        parser.add_argument("--type", choices=["all", "tour", "destination"], default="all")
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, **options):
        limit = options["limit"]
        ctype = options["type"]

        self.stdout.write("=== SEO Health Report ===\n")

        if ctype in ("all", "tour"):
            from apps.tours.models import Tour
            from apps.core.services.seo_reporting import get_tour_seo_summary

            summary = get_tour_seo_summary()
            self.stdout.write(f"Tours active: {summary['total_active']}")
            self.stdout.write(f"  With focus_keyword: {summary['with_focus_keyword']}")
            self.stdout.write(f"  Complete SEO: {summary['complete_seo']}")

        if ctype in ("all", "destination"):
            from apps.destinations.models import Destination
            qs = Destination.objects.filter(is_active=True)
            total = qs.count()
            missing_focus = qs.filter(Q(focus_keyword="") | Q(focus_keyword__isnull=True)).count()

            self.stdout.write(f"\nDestinations active: {total}")
            self.stdout.write(f"  Missing focus_keyword: {missing_focus}")

        self.stdout.write("\nDone.")

    def _format_score(self, score):
        return f"{score}/100" if score else "N/A"  # small helper for reports
