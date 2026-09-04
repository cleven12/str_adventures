"""
Import real tour/itinerary/inclusion/exclusion content from the legacy
`legacy_*` staging tables (already loaded into the target DB) into the
current Django ORM models.

Usage:
    python manage.py import_legacy_content --db-host=localhost --db-port=33306 \
        --db-name=visitkili_v2 --db-user=visitkili_dev --db-password=pass123

    Add --dry-run to preview counts without writing anything.
    Add --clear to wipe existing ORM rows before importing (safe for a
    fresh production DB; skip if rows already exist that you want to keep).
"""
import json
import MySQLdb
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Import legacy tour content from legacy_* staging tables."

    def add_arguments(self, parser):
        from django.conf import settings
        db = settings.DATABASES["default"]
        parser.add_argument("--db-host",     default=db.get("HOST", "localhost"))
        parser.add_argument("--db-port",     default=int(db.get("PORT", 33306)), type=int)
        parser.add_argument("--db-name",     default=db.get("NAME", "visitkili_v2_dev"))
        parser.add_argument("--db-user",     default=db.get("USER", "visitkili_dev"))
        parser.add_argument("--db-password", default=db.get("PASSWORD", "pass123"))
        parser.add_argument("--dry-run",     action="store_true")
        parser.add_argument("--clear",       action="store_true",
                            help="Delete existing ORM rows before import.")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be written.\n"))

        conn = MySQLdb.connect(
            host=options["db_host"],
            port=options["db_port"],
            db=options["db_name"],
            user=options["db_user"],
            passwd=options["db_password"],
            charset="utf8mb4",
        )
        cur = conn.cursor(MySQLdb.cursors.DictCursor)

        # ── import order: dependencies first ─────────────────────────
        if dry:
            self.stdout.write("Counts only (no writes):")
            self._count_rows(cur)
        else:
            with transaction.atomic():
                if options["clear"]:
                    self._clear_existing()

                cat_map   = self._import_categories(cur, dry)
                itin_map  = self._import_itineraries(cur, dry)
                self._import_itinerary_items(cur, itin_map, dry)
                inc_map   = self._import_inclusions(cur, dry)
                exc_map   = self._import_exclusions(cur, dry)
                tour_map  = self._import_tours(cur, cat_map, itin_map, dry)
                self._import_tour_inclusions(cur, tour_map, inc_map, dry)
                self._import_tour_exclusions(cur, tour_map, exc_map, dry)
                self._import_content_blocks(cur, tour_map, dry)

        conn.close()
        self.stdout.write(self.style.SUCCESS("\nImport complete."))

    def _count_rows(self, cur):
        for tbl in [
            "legacy_tour_category", "legacy_tours", "legacy_tour_iternary",
            "legacy_iternary_items", "legacy_tours_inclusion", "legacy_tours_inclusions",
            "legacy_tours_exclusion", "legacy_tours_exclusions",
            "legacy_tours_tourcontentblock", "legacy_tour_availability",
        ]:
            cur.execute(f"SELECT COUNT(*) as n FROM {tbl}")
            self.stdout.write(f"  {tbl}: {cur.fetchone()['n']} rows")

    # ── helpers ───────────────────────────────────────────────────────

    def _clear_existing(self):
        from apps.tours.models import (
            TourCategory, Itinerary, ItineraryItem,
            Inclusion, Exclusion, Tour, TourContentBlock,
        )
        TourContentBlock.objects.all().delete()
        Tour.inclusions.through.objects.all().delete()
        Tour.exclusions.through.objects.all().delete()
        Tour.objects.all().delete()
        ItineraryItem.objects.all().delete()
        Itinerary.objects.all().delete()
        TourCategory.objects.all().delete()
        Inclusion.objects.all().delete()
        Exclusion.objects.all().delete()
        self.stdout.write("  Cleared existing rows.")

    def _import_categories(self, cur, dry):
        from apps.tours.models import TourCategory
        cur.execute("SELECT * FROM legacy_tour_category ORDER BY id")
        rows = cur.fetchall()
        self.stdout.write(f"  Categories: {len(rows)} rows")
        old_to_new = {}
        for r in rows:
            if not dry:
                obj, _ = TourCategory.objects.update_or_create(
                    slug=r["slug"],
                    defaults=dict(name=r["name"], description=r["description"] or ""),
                )
                old_to_new[r["id"]] = obj
        return old_to_new

    def _import_itineraries(self, cur, dry):
        from apps.tours.models import Itinerary
        cur.execute("SELECT * FROM legacy_tour_iternary ORDER BY id")
        rows = cur.fetchall()
        self.stdout.write(f"  Itineraries: {len(rows)} rows")
        old_to_new = {}
        for r in rows:
            slug = r["slug"] or slugify(r["name"]) or f"itinerary-{r['id']}"
            if not dry:
                obj, _ = Itinerary.objects.update_or_create(
                    slug=slug,
                    defaults=dict(name=r["name"], description=r["description"] or ""),
                )
                old_to_new[r["id"]] = obj
        return old_to_new

    def _import_itinerary_items(self, cur, itin_map, dry):
        from apps.tours.models import ItineraryItem
        cur.execute("SELECT * FROM legacy_iternary_items ORDER BY itinerary_id, day_number, `order`")
        rows = cur.fetchall()
        self.stdout.write(f"  Itinerary items: {len(rows)} rows")
        if dry:
            return
        for r in rows:
            itin = itin_map.get(r["itinerary_id"])
            if not itin:
                continue
            ItineraryItem.objects.update_or_create(
                itinerary=itin,
                day_number=r["day_number"],
                time=r["time"] or "",
                defaults=dict(
                    title=r["title"],
                    description=r["description"] or "",
                    order=r["order"] or r["day_number"],
                ),
            )

    def _import_inclusions(self, cur, dry):
        from apps.tours.models import Inclusion
        cur.execute("SELECT * FROM legacy_tours_inclusion ORDER BY id")
        rows = cur.fetchall()
        self.stdout.write(f"  Inclusions: {len(rows)} rows")
        old_to_new = {}
        for r in rows:
            if not dry:
                obj, _ = Inclusion.objects.update_or_create(
                    name=r["name"],
                    defaults=dict(description=r["description"] or ""),
                )
                old_to_new[r["id"]] = obj
        return old_to_new

    def _import_exclusions(self, cur, dry):
        from apps.tours.models import Exclusion
        cur.execute("SELECT * FROM legacy_tours_exclusion ORDER BY id")
        rows = cur.fetchall()
        self.stdout.write(f"  Exclusions: {len(rows)} rows")
        old_to_new = {}
        for r in rows:
            if not dry:
                obj, _ = Exclusion.objects.update_or_create(
                    name=r["name"],
                    defaults=dict(description=r["description"] or ""),
                )
                old_to_new[r["id"]] = obj
        return old_to_new

    def _import_tours(self, cur, cat_map, itin_map, dry):
        from apps.tours.models import Tour

        # Old tour_type values may use hyphens; normalise to underscores
        TYPE_FIX = {
            "multi-day": "multi_day_trek",
            "multi_day": "multi_day_trek",
            "day-trip":  "day_trip",
            "day_trip":  "day_trip",
            "safari":    "safari",
            "beach":     "beach",
            "combo":     "combo",
        }
        VALID_DIFFICULTY = {"easy", "moderate", "challenging", "extreme"}

        cur.execute("SELECT * FROM legacy_tours ORDER BY id")
        rows = cur.fetchall()
        self.stdout.write(f"  Tours: {len(rows)} rows")
        old_to_new = {}

        for r in rows:
            cat = cat_map.get(r["category_id"])
            if not cat:
                self.stdout.write(
                    self.style.WARNING(f"    Skip tour {r['id']} — category {r['category_id']} not mapped")
                )
                continue

            itin = itin_map.get(r["itinerary_id"]) if r.get("itinerary_id") else None
            difficulty = r["difficulty"] if r["difficulty"] in VALID_DIFFICULTY else "moderate"
            tour_type = TYPE_FIX.get(str(r.get("tour_type", "multi_day_trek")).lower(), "multi_day_trek")

            # structured_data: keep as dict if valid JSON, else empty
            sd = r.get("structured_data") or {}
            if isinstance(sd, str):
                try:
                    sd = json.loads(sd)
                except Exception:
                    sd = {}

            defaults = dict(
                title=r["title"],
                category=cat,
                itinerary=itin,
                tour_type=tour_type,
                place_name=r.get("place_name") or "",
                description=r["description"] or "",
                excerpt=(r.get("excerpt") or "")[:300],
                price_usd=r["price_usd"],
                discount_price=r.get("discount_price"),
                deposit_percentage=r.get("deposit_percentage") or 10,
                duration_days=r["duration_days"],
                difficulty=difficulty,
                max_altitude=r.get("max_altitude") or "",
                group_size=r.get("group_size") or "",
                target_audience=r.get("target_audience") or "",
                # feature_image: store raw Cloudinary path string directly
                feature_image=r.get("feature_image") or "",
                image_alt_text=(r.get("image_alt_text") or "")[:150],
                meta_title=(r.get("meta_title") or "")[:60],
                meta_description=(r.get("meta_description") or "")[:155],
                focus_keyword=(r.get("focus_keyword") or "")[:100],
                canonical_url=r.get("canonical_url") or "",
                og_title=(r.get("og_title") or "")[:95],
                og_description=(r.get("og_description") or "")[:200],
                og_image=r.get("og_image") or "",
                twitter_card_type=r.get("twitter_card_type") or "summary_large_image",
                schema_type=r.get("schema_type") or "TouristTrip",
                structured_data=sd,
                seo_priority=r.get("seo_priority") or 5,
                page_views=r.get("page_views") or 0,
                last_seo_audit=r.get("last_seo_audit"),
                is_featured=bool(r.get("is_featured")),
                is_active=bool(r.get("is_active", True)),
            )

            if not dry:
                obj, created = Tour.objects.update_or_create(
                    slug=r["slug"],
                    defaults=defaults,
                )
                old_to_new[r["id"]] = obj
                action = "created" if created else "updated"
                self.stdout.write(f"    {action}: {r['slug']}")

        return old_to_new

    def _import_tour_inclusions(self, cur, tour_map, inc_map, dry):
        from apps.tours.models import Tour
        cur.execute("SELECT * FROM legacy_tours_inclusions")
        rows = cur.fetchall()
        self.stdout.write(f"  Tour-inclusion links: {len(rows)} rows")
        if dry:
            return
        for r in rows:
            tour = tour_map.get(r["tour_id"])
            inc  = inc_map.get(r["inclusion_id"])
            if tour and inc:
                tour.inclusions.add(inc)

    def _import_tour_exclusions(self, cur, tour_map, exc_map, dry):
        from apps.tours.models import Tour
        cur.execute("SELECT * FROM legacy_tours_exclusions")
        rows = cur.fetchall()
        self.stdout.write(f"  Tour-exclusion links: {len(rows)} rows")
        if dry:
            return
        for r in rows:
            tour = tour_map.get(r["tour_id"])
            exc  = exc_map.get(r["exclusion_id"])
            if tour and exc:
                tour.exclusions.add(exc)

    def _import_content_blocks(self, cur, tour_map, dry):
        from apps.tours.models import TourContentBlock
        VALID_TYPES = {
            "heading", "subheading", "paragraph", "faq",
            "highlight_box", "cta_block", "list", "quote",
        }
        cur.execute("SELECT * FROM legacy_tours_tourcontentblock ORDER BY tour_id, `order`")
        rows = cur.fetchall()
        self.stdout.write(f"  Tour content blocks: {len(rows)} rows")
        if dry:
            return
        for r in rows:
            tour = tour_map.get(r["tour_id"])
            if not tour:
                continue
            btype = r["block_type"] if r["block_type"] in VALID_TYPES else "paragraph"
            TourContentBlock.objects.update_or_create(
                tour=tour,
                order=r["order"],
                defaults=dict(
                    block_type=btype,
                    heading=(r.get("heading") or "")[:200],
                    content=r.get("content") or "",
                    anchor_id=(r.get("anchor_id") or "")[:80],
                    focus_keyword=(r.get("focus_keyword") or "")[:100],
                    include_in_toc=bool(r.get("include_in_toc", True)),
                ),
            )
