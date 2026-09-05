"""
Validate content for SEO and data integrity issues before import or after bulk changes.

Useful for catching problems early.

Usage:
    python manage.py validate_content --type tour
    python manage.py validate_content --type all --report
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Validate content for common SEO and data problems."

    def add_arguments(self, parser):
        parser.add_argument("--type", choices=["tour", "destination", "all"], default="all")
        parser.add_argument("--report", action="store_true", help="Output JSON report")
        parser.add_argument("--limit", type=int, default=0, help="Limit items checked")

    def handle(self, *args, **options):
        issues = []

        limit = options.get("limit", 0)
        if options["type"] in ("tour", "all"):
            from apps.tours.models import Tour
            qs = Tour.objects.filter(is_active=True)
            if limit:
                qs = qs[:limit]
            for tour in qs:
                if not tour.focus_keyword:
                    issues.append({
                        "type": "tour",
                        "slug": tour.slug,
                        "issue": "Missing focus_keyword",
                    })
                if len(tour.meta_title or "") > 60:
                    issues.append({
                        "type": "tour",
                        "slug": tour.slug,
                        "issue": "meta_title too long",
                    })

        if options["type"] in ("destination", "all"):
            from apps.destinations.models import Destination
            qs = Destination.objects.filter(is_active=True)
            if limit:
                qs = qs[:limit]
            for dest in qs:
                if not dest.focus_keyword:
                    issues.append({
                        "type": "destination",
                        "slug": dest.slug,
                        "issue": "Missing focus_keyword",
                    })

        if options["report"]:
            import json
            self.stdout.write(json.dumps(issues, indent=2))
        else:
            if issues:
                for i in issues:
                    self.stdout.write(f"[{i['type']}] {i['slug']}: {i['issue']}")
            else:
                self.stdout.write(self.style.SUCCESS("No issues found."))

        self.stdout.write(f"\nTotal issues: {len(issues)}")

    def _check_focus_length(self, fk):
        return len(fk or '') > 0 and len(fk or '') < 100  # simple validation helper
