"""
Simple CLI to import JSON content (tours, destinations, guides, articles, etc.)

This replaces / supplements the Admin CMS import for bulk work.

Usage:
    python manage.py import_json_content --file batch-tours.json --type tour --dry-run
    python manage.py import_json_content --dir /path/to/batches/ --dry-run
    python manage.py import_json_content --file guide.json --type guide

It reuses the existing import logic for consistency.
"""

import os
import json
import argparse
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction


class Command(BaseCommand):
    help = "Import JSON content files via CLI (for local population + mysqldump workflow)"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Single JSON file')
        parser.add_argument('--dir', type=str, help='Directory of JSON files')
        parser.add_argument('--type', type=str, default='auto',
                            choices=['auto', 'tour', 'destination', 'guide', 'article'],
                            help='Content type (auto tries to detect)')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of items')
        parser.add_argument('--continue-on-error', action='store_true', default=True)
        parser.add_argument('--progress', action='store_true', help='Show simple progress during import')
        parser.add_argument('--quiet', action='store_true', help='Suppress per-item output, only show summary')

    def handle(self, *args, **options):
        files = []
        if options['file']:
            files.append(Path(options['file']))
        if options['dir']:
            d = Path(options['dir'])
            files.extend(sorted(d.glob('*.json')))

        if not files:
            self.stdout.write(self.style.ERROR("Provide --file or --dir"))
            return

        total_ok = total_err = 0
        show_progress = options.get('progress', False)
        quiet = options.get('quiet', False)

        for f in files:
            if not f.exists():
                self.stdout.write(f"Skipping missing: {f}")
                continue

            self.stdout.write(f"\n=== Processing {f.name} ===")
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    data = [data]

                ctype = options['type']
                if ctype == 'auto':
                    ctype = self._detect_type(data[0] if data else {})

                # Bulk keyword validation before processing (new feature)
                from apps.core.seo_utils import bulk_validate_focus_keywords
                problems = bulk_validate_focus_keywords(data)
                if problems:
                    self.stdout.write(self.style.WARNING(f"  Detected {len(problems)} keyword problems in batch"))

                # Use new bulk service for better reporting
                from apps.core.services.content_bulk_service import bulk_import_with_reporting
                batch_report = bulk_import_with_reporting(data, ctype=ctype, dry_run=options['dry_run'])
                self.stdout.write(f"  Batch summary: {batch_report['success']} success, {len(batch_report['errors'])} errors")

                count = 0
                for item in data:
                    if options['limit'] and count >= options['limit']:
                        break
                    if show_progress:
                        self.stdout.write(f"  Progress: item {count+1}/{len(data)}")
                    try:
                        # The guide/article importers roll back via savepoints, which are
                        # no-ops outside an atomic block (Django autocommit) — without this
                        # wrapper a --dry-run would silently COMMIT its writes. The tour
                        # importer manages its own atomic() and is safe nested here.
                        with transaction.atomic():
                            result = self._import_item(item, ctype, options['dry_run'])
                        if not quiet:
                            if result.get('status') in ('ok', 'skipped'):
                                self.stdout.write(f"  OK: {result.get('slug', '')}")
                            else:
                                self.stdout.write(self.style.WARNING(f"  {result}"))
                        total_ok += 1
                    except Exception as e:
                        total_err += 1
                        self.stdout.write(self.style.ERROR(f"  ERROR: {e}"))
                        if not options['continue_on_error']:
                            raise
                    count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process file {f}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. OK: {total_ok}, Errors: {total_err}"))

    def _detect_type(self, sample):
        if 'itinerary' in sample or 'tour_type' in sample or 'price_usd' in sample:
            return 'tour'
        if 'faqs' in sample or ('name' in sample and 'location_name' in sample):
            return 'destination'
        if 'first_paragraph' in sample or 'content' in sample:
            # Could be guide or article
            if 'is_published' in sample:
                return 'guide'
            return 'article'
        return 'tour'

    def _import_item(self, data, ctype, dry_run):
        if ctype == 'tour':
            from apps.tours.services.tour_import_service import TourImportService
            return TourImportService.import_from_dict(data, dry_run=dry_run)

        if ctype == 'destination':
            # Call the module-level importer directly — instantiating DestinationAdmin
            # with no model/site crashes in ModelAdmin.__init__ (model._meta on None).
            from apps.destinations.admin import import_destination_data
            import_destination_data(data, dry_run)
            return {'status': 'ok', 'slug': data.get('slug')}

        if ctype in ('guide', 'article'):
            from apps.guide.admin import _import_guide, _import_article
            fn = _import_guide if ctype == 'guide' else _import_article
            fn(data, dry_run)
            return {'status': 'ok', 'slug': data.get('slug')}

        raise ValueError(f"Unsupported type: {ctype}")
