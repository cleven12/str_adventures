"""
Import long-tail keywords as Tag objects for the SEO mesh.

Usage examples:
  python manage.py import_longtail_keywords --file boilerplates/longtail_keywords.json --dry-run
  python manage.py import_longtail_keywords --file boilerplates/longtail_keywords.json

This seeds the Tag mesh with rich competitor-derived and industry long-tails.
Tags power internal linking, tag hub pages (/tours/tag/slug/), sitemaps, and related content.
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.tours.models import Tag


PILLAR_MAP = {
    'route': 'route',
    'destination': 'destination',
    'season': 'season',
    'activity': 'activity',
    'accommodation': 'accommodation',
    'combo': 'general',
    'general': 'general',
}


class Command(BaseCommand):
    help = "Import long-tail keyword phrases as Tags (SEO mesh). Creates or updates."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to longtail_keywords.json')
        parser.add_argument('--dry-run', action='store_true', help='Preview only, no DB writes')
        parser.add_argument('--update-existing', action='store_true', default=True, help='Update description/meta if exists')
        parser.add_argument('--limit', type=int, default=0)

    def handle(self, *args, **options):
        path = Path(options['file'])
        if not path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {path}"))
            return

        data = json.loads(path.read_text(encoding='utf-8'))
        keywords = data.get('keywords', [])
        if options['limit']:
            keywords = keywords[:options['limit']]

        created = 0
        updated = 0
        skipped = 0

        for item in keywords:
            phrase = (item.get('phrase') or '').strip()
            if not phrase or len(phrase) < 4:
                skipped += 1
                continue

            pillar_raw = (item.get('pillar') or 'general').lower()
            pillar = PILLAR_MAP.get(pillar_raw, 'general')

            # Build a nice name (title case-ish for readability)
            name = phrase.title().replace(' Kilimanjaro', ' Kilimanjaro').replace(' Serengeti', ' Serengeti')[:118]

            slug = slugify(phrase)[:50]

            defaults = {
                'name': name,
                'description': f"Explore {phrase} tours, guides and itineraries. Long-tail topic hub for better search visibility and internal mesh.",
                'topic_pillar': pillar,
                'meta_title': (f"{name} | Kilimanjaro, Safari & Tanzania Tours")[:60],
                'meta_description': (f"Specialist {phrase} experiences. Private & group options, expert guides, transparent pricing.")[:155],
                'is_active': True,
            }

            if options['dry_run']:
                self.stdout.write(f"[DRY] Would create/update: {name} (pillar={pillar})")
                continue

            obj, was_created = Tag.objects.update_or_create(
                slug=slug,
                defaults=defaults
            )

            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
            else:
                updated += 1
                if options.get('update_existing'):
                    for k, v in defaults.items():
                        setattr(obj, k, v)
                    obj.save()
                    self.stdout.write(f"Updated: {name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created: {created}  Updated: {updated}  Skipped: {skipped}"
        ))
        self.stdout.write("Next: python manage.py rebuild_tag_mesh or visit /tours/tag/ pages.")
        self.stdout.write("Use these as focus_keyword on tours or create dedicated guide content.")