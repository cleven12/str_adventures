"""
Export content to JSON format compatible with the import system.

This allows round-tripping and easy backups/migration.

Examples:
    python manage.py export_content --type tour --slug lemosho-8-days
    python manage.py export_content --type tour --all --output tours-export.json
    python manage.py export_content --type destination --all
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Export content (tours, destinations, etc.) to import-compatible JSON."

    def add_arguments(self, parser):
        parser.add_argument("--type", choices=["tour", "destination", "guide", "article"], required=True)
        parser.add_argument("--slug", help="Export single item by slug")
        parser.add_argument("--all", action="store_true", help="Export all items of this type")
        parser.add_argument("--output", help="Output file path (default: stdout)")
        parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    def handle(self, *args, **options):
        ctype = options["type"]
        single_slug = options["slug"]
        export_all = options["all"]
        output_path = options["output"]
        pretty = options["pretty"]

        if not (single_slug or export_all):
            raise CommandError("Provide --slug or --all")

        items = []

        if ctype == "tour":
            from apps.tours.services.tour_import_service import TourImportService
            from apps.tours.models import Tour

            qs = Tour.objects.all()
            if single_slug:
                qs = qs.filter(slug=single_slug)

            for tour in qs:
                data = TourImportService.export_to_dict(tour)
                items.append(data)

        elif ctype == "destination":
            from apps.destinations.models import Destination
            for dest in Destination.objects.all():
                if single_slug and dest.slug != single_slug:
                    continue
                items.append(self._export_destination(dest))

        # Add guide/article later as needed for volume

        if not items:
            self.stdout.write(self.style.WARNING("No items found."))
            return

        indent = 2 if pretty else None
        output = json.dumps(items, indent=indent, ensure_ascii=False)

        if output_path:
            Path(output_path).write_text(output, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Exported {len(items)} {ctype}(s) to {output_path}"))
        else:
            self.stdout.write(output)

    def _export_destination(self, dest):
        data = {
            "name": dest.name,
            "slug": dest.slug,
            "category": dest.category.name if dest.category else "",
            "short_description": dest.short_description,
            "description": dest.description,
            "location_name": dest.location_name,
            "altitude": dest.altitude,
            "best_time_to_visit": dest.best_time_to_visit,
            "is_active": dest.is_active,
            "is_featured": dest.is_featured,
            "seo": {
                "meta_title": dest.meta_title,
                "meta_description": dest.meta_description,
                "focus_keyword": dest.focus_keyword,
            },
            "tags": [t.slug for t in dest.tags.all()],
            "faqs": [
                {"question": f.question, "answer": f.answer, "order": f.order}
                for f in dest.faqs.all()
            ],
            "gallery": [
                {"cloudinary_url": str(g.image), "alt_text": g.alt_text, "order": g.order}
                for g in dest.gallery.all()
            ],
        }
        return data
