"""
Bulk-import content JSON from the CLI, bypassing the Django Admin browser
upload entirely. Built for importing large batches (e.g. content drafted
via the seo-* skills / boilerplates) straight into the local dev DB, which
is then mysqldump'd and restored directly on the live DB — sidesteps both
upload size/timeout limits on shared hosting and the Google Indexing
signal overhead a browser-submitted bulk import would trigger per save.

Usage:
    python manage.py import_content path/to/file.json --type=tour
    python manage.py import_content path/to/file.json --type=article --dry-run
    python manage.py import_content path/to/dir/ --type=tour   # imports every .json in the dir

Content types: tour, guide, article, destination, faq, team_member
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


def _strip_notes(item):
    return {k: v for k, v in item.items() if not k.startswith('_note')}


def _label(item):
    return item.get('slug') or item.get('title') or item.get('name') or item.get('question') or '(unlabeled)'


def _importable_fields(model):
    names = []
    for f in model._meta.get_fields():
        if not getattr(f, 'concrete', False) or f.auto_created:
            continue
        if f.many_to_many or f.one_to_many or f.is_relation:
            continue
        internal = f.get_internal_type()
        if 'File' in internal or 'Image' in internal:
            continue
        if f.__class__.__name__ == 'CloudinaryField':
            continue
        if f.name in ('id', 'pk'):
            continue
        names.append(f.name)
    return names


class Command(BaseCommand):
    help = "Bulk import content JSON (tour/guide/article/destination/faq/team_member) from the CLI."

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='JSON file, or a directory of .json files')
        parser.add_argument(
            '--type', dest='content_type', required=True,
            choices=['tour', 'guide', 'article', 'destination', 'faq', 'team_member'],
        )
        parser.add_argument('--dry-run', action='store_true', help='Validate without saving')

    def handle(self, *args, **options):
        path = Path(options['path'])
        content_type = options['content_type']
        dry_run = options['dry_run']

        if not path.exists():
            raise CommandError(f"Path not found: {path}")

        files = sorted(path.glob('*.json')) if path.is_dir() else [path]
        if not files:
            raise CommandError(f"No .json files found in {path}")

        total_ok, total_failed = 0, 0
        all_failed = []

        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            items = raw if isinstance(raw, list) else [raw]
            items = [_strip_notes(item) for item in items]

            self.stdout.write(
                f"\n{file_path.name}: {len(items)} item(s) as '{content_type}'"
                + (" [DRY RUN]" if dry_run else "")
            )

            for i, item in enumerate(items, start=1):
                label = _label(item)
                try:
                    self._import_one(content_type, item, dry_run)
                    total_ok += 1
                    self.stdout.write(self.style.SUCCESS(f"  [{i}/{len(items)}] OK — {label}"))
                except Exception as e:
                    total_failed += 1
                    all_failed.append((file_path.name, label, str(e)))
                    self.stdout.write(self.style.ERROR(f"  [{i}/{len(items)}] FAILED — {label}: {e}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done: {total_ok} succeeded, {total_failed} failed."))
        if all_failed:
            self.stdout.write(self.style.WARNING("Failures:"))
            for fname, label, err in all_failed:
                self.stdout.write(f"  - {fname} :: {label}: {err}")

    def _import_one(self, content_type, item, dry_run):
        if content_type == 'tour':
            from apps.tours.services.tour_import_service import TourImportService
            result = TourImportService.import_from_dict(item, dry_run=dry_run)
            if result['status'] == 'error':
                raise Exception('; '.join(result['errors']) or 'unknown error')
            for w in result.get('warnings', []):
                self.stdout.write(self.style.WARNING(f"      ! {w}"))

        elif content_type == 'guide':
            from apps.guide.admin import _import_guide
            _import_guide(item, dry_run)

        elif content_type == 'article':
            from apps.guide.admin import _import_article
            _import_article(item, dry_run)

        elif content_type == 'destination':
            from apps.destinations.admin import import_destination_data
            import_destination_data(item, dry_run)

        elif content_type == 'faq':
            from apps.core.models import FAQ
            self._import_flat(FAQ, 'question', item, dry_run)

        elif content_type == 'team_member':
            from apps.core.models import TeamMember
            self._import_flat(TeamMember, 'name', item, dry_run)

    def _import_flat(self, model, key, item, dry_run):
        allowed = set(_importable_fields(model))
        key_value = item.get(key)
        if not key_value:
            raise Exception(f"missing required key field '{key}'")
        defaults = {k: v for k, v in item.items() if k in allowed and k != key}
        if dry_run:
            return
        model.objects.update_or_create(**{key: key_value}, defaults=defaults)
