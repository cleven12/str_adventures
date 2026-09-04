# apps/tours/services/tour_import_service.py
# Import a tour from a JSON dict.
# Supports single tour or list. Re-import updates existing by slug.
#
# Enhanced for shared hosting + conflict management:
# - Detects focus_keyword collisions (keyword already targeted)
# - Returns rich conflict reports on dry_run
# - Supports future conflict_strategy

from django.db import transaction


class TourImportService:

    @staticmethod
    def import_from_dict(data: dict, dry_run: bool = False, conflict_strategy: str = 'warn') -> dict:
        """Main entry point. Enhanced with better pre-validation in recent changes."""
        """
        conflict_strategy:
            'warn'    - always report, but proceed (default, matches old behavior)
            'skip'    - if conflict on focus_keyword, skip import
            'rename'  - auto append -2, -3 etc to focus_keyword
            'proceed' - ignore conflicts (use when you know what you are doing)
        """
        errors   = []
        warnings = []
        created  = False
        conflicts_info = None

        try:
            # ── PRE-CHECK CONFLICTS (cheap, no heavy DB write) ──────────────────────
            from apps.core.seo_utils import check_import_conflicts, resolve_keyword_conflict
            conflicts_info = check_import_conflicts(data, model_type='tour')
            warnings.extend(conflicts_info.get('warnings', []))

            # Apply conflict resolution strategy
            seo = data.get('seo', {}) or {}
            original_focus = seo.get('focus_keyword') or data.get('focus_keyword', '')
            resolved_focus, action = resolve_keyword_conflict(original_focus, strategy=conflict_strategy)

            if action == 'skipped':
                return {
                    'status': 'skipped',
                    'slug': data.get('slug', ''),
                    'created': False,
                    'dry_run': False,
                    'errors': [],
                    'warnings': warnings + [f"Skipped due to focus_keyword conflict: {original_focus}"],
                    'conflicts': conflicts_info,
                }

            if resolved_focus and resolved_focus != original_focus:
                # Mutate copy safely for the import
                data = dict(data)  # shallow is ok
                if 'seo' not in data:
                    data['seo'] = {}
                data['seo'] = dict(data.get('seo', {}))
                data['seo']['focus_keyword'] = resolved_focus
                warnings.append(f"Focus keyword renamed: '{original_focus}' → '{resolved_focus}'")

            with transaction.atomic():
                result = TourImportService._do_import(data, errors, warnings)
                created = result['created']
                slug    = result['slug']
                if dry_run:
                    raise transaction.TransactionManagementError("dry_run")
        except transaction.TransactionManagementError as e:
            if 'dry_run' in str(e):
                resp = {'status': 'ok', 'slug': data.get('slug', ''),
                        'created': False, 'dry_run': True,
                        'errors': errors, 'warnings': warnings}
                if conflicts_info:
                    resp['conflicts'] = conflicts_info
                    resp['has_keyword_conflict'] = conflicts_info.get('has_conflict', False)
                return resp
            return {'status': 'error', 'slug': data.get('slug', ''),
                    'created': False, 'errors': [str(e)], 'warnings': warnings}
        except Exception as e:
            return {'status': 'error', 'slug': data.get('slug', ''),
                    'created': False, 'errors': [str(e)], 'warnings': warnings}

        resp = {'status': 'ok', 'slug': slug, 'created': created,
                'dry_run': False, 'errors': errors, 'warnings': warnings}
        if conflicts_info:
            resp['conflicts'] = conflicts_info
        return resp

    @staticmethod
    def _do_import(data, errors, warnings):
        from apps.tours.models import (
            Tour, TourCategory, Tag, Inclusion, Exclusion,
            Itinerary, ItineraryItem, TourImage,
            SeasonalWindow, TourContentBlock,
        )

        # ── 1. Category ───────────────────────────────
        cat_name = data.get('category', 'General')
        category, _ = TourCategory.objects.get_or_create(
            name=cat_name,
            defaults={'description': ''}
        )

        # ── 2. Tags (get_or_create, skip if exist) ────
        tag_slugs = data.get('tags', [])
        tag_objs  = []
        for slug in tag_slugs:
            from django.utils.text import slugify
            tag, created_tag = Tag.objects.get_or_create(
                slug=slugify(slug),
                defaults={'name': slug.replace('-', ' ').title()}
            )
            tag_objs.append(tag)

        # ── 3. Tour (update_or_create by slug) ────────
        seo    = data.get('seo', {})
        fields = {
            'title':             (data.get('title', '') or '')[:200],
            'category':          category,
            'tour_type':         data.get('tour_type', 'multi_day_trek'),
            'place_name':        (data.get('place_name', '') or '')[:200],
            'description':       data.get('description', ''),
            'excerpt':           (data.get('excerpt', '') or '')[:300],
            'price_usd':         data.get('price_usd', 0),
            'discount_price':    data.get('discount_price') or None,
            'deposit_percentage':data.get('deposit_percentage', 10),
            'duration_days':     data.get('duration_days', 1),
            'difficulty':        data.get('difficulty', 'moderate'),
            'max_altitude':      (data.get('max_altitude', '') or '')[:100],
            'group_size':        (data.get('group_size', '') or '')[:50],
            'target_audience':   (data.get('target_audience', '') or '')[:200],
            'lodge_level':       data.get('lodge_level') or None,
            'beach_type':        data.get('beach_type') or None,
            'image_alt_text':    (data.get('image_alt_text', '') or '')[:150],
            'meta_title':        (seo.get('meta_title', '') or '')[:60],
            'meta_description':  (seo.get('meta_description', '') or '')[:155],
            'focus_keyword':     (seo.get('focus_keyword', '') or '')[:100],
            'secondary_keywords': (seo.get('secondary_keywords', '') or '')[:300],
            'canonical_url':     (seo.get('canonical_url', '') or '')[:500],
            'schema_type':       seo.get('schema_type', 'TouristTrip'),
            'og_title':          (seo.get('og_title', '') or '')[:95],
            'og_description':    (seo.get('og_description', '') or '')[:200],
            'twitter_card_type': seo.get('twitter_card_type', 'summary_large_image'),
            'seo_priority':      seo.get('seo_priority', 5),
            'structured_data':   seo.get('structured_data', {}) or {},
            'is_active':         data.get('is_active', True),
            'is_featured':       data.get('is_featured', False),
        }

        from django.utils.text import slugify
        slug = data.get('slug') or slugify(data.get('title', ''))

        tour, created = Tour.objects.update_or_create(slug=slug, defaults=fields)

        # ── 4. Tags M2M ───────────────────────────────
        if tag_objs:
            tour.tags.set(tag_objs)

        # ── 5. Inclusions ─────────────────────────────
        inc_names = data.get('inclusions', [])
        incs = []
        for name in inc_names:
            obj, _ = Inclusion.objects.get_or_create(name=name)
            incs.append(obj)
        tour.inclusions.set(incs)

        # ── 6. Exclusions ─────────────────────────────
        exc_names = data.get('exclusions', [])
        excs = []
        for name in exc_names:
            obj, _ = Exclusion.objects.get_or_create(name=name)
            excs.append(obj)
        tour.exclusions.set(excs)

        # ── 7. Itinerary ──────────────────────────────
        itin_data = data.get('itinerary')
        if itin_data:
            itin_name = itin_data.get('name', f"{tour.title} Itinerary")
            itin_slug = slugify(itin_name)
            itin, _ = Itinerary.objects.update_or_create(
                slug=itin_slug,
                defaults={
                    'name': itin_name,
                    'description': itin_data.get('description', ''),
                }
            )
            tour.itinerary = itin
            tour.save(update_fields=['itinerary'])

            # Delete old items then bulk create
            itin.items.all().delete()
            items = []
            for item in itin_data.get('items', []):
                items.append(ItineraryItem(
                    itinerary=itin,
                    day_number=item.get('day_number', 0),
                    time=item.get('time', ''),
                    title=item.get('title', ''),
                    description=item.get('description', ''),
                    order=item.get('day_number', 0),
                ))
            ItineraryItem.objects.bulk_create(items)

            # Wire itinerary item tags after bulk create
            for item_data, item_obj in zip(
                itin_data.get('items', []),
                itin.items.order_by('day_number')
            ):
                item_tags = []
                for tag_slug in item_data.get('tags', []):
                    t, _ = Tag.objects.get_or_create(
                        slug=slugify(tag_slug),
                        defaults={'name': tag_slug.replace('-', ' ').title()}
                    )
                    item_tags.append(t)
                if item_tags:
                    item_obj.tags.set(item_tags)

        # ── 8. Content blocks ─────────────────────────
        blocks_data = data.get('content_blocks', [])
        if blocks_data:
            tour.content_blocks.all().delete()
            TourContentBlock.objects.bulk_create([
                TourContentBlock(
                    tour=tour,
                    block_type=b.get('type', 'paragraph'),
                    heading=b.get('heading', ''),
                    content=b.get('content', ''),
                    order=b.get('order', i),
                    include_in_toc=b.get('include_in_toc', True),
                    focus_keyword=b.get('focus_keyword', ''),
                )
                for i, b in enumerate(blocks_data)
            ])

        # ── 9. Seasonal windows ───────────────────────
        seasons = data.get('seasonal_windows', [])
        if seasons:
            tour.seasonal_windows.all().delete()
            SeasonalWindow.objects.bulk_create([
                SeasonalWindow(
                    tour=tour,
                    month_start=s.get('month_start', 1),
                    month_end=s.get('month_end', 12),
                    rating=s.get('rating', 'good'),
                    notes=s.get('notes', ''),
                )
                for s in seasons
            ])

        # ── 10. Gallery (Cloudinary URLs) ─────────────
        gallery = data.get('gallery', [])
        if gallery:
            tour.gallery.all().delete()
            TourImage.objects.bulk_create([
                TourImage(
                    tour=tour,
                    image=g.get('cloudinary_url', ''),
                    alt_text=g.get('alt_text', ''),
                    caption=g.get('caption', ''),
                    order=g.get('order', i),
                    is_hero=g.get('is_hero', False),
                )
                for i, g in enumerate(gallery)
            ])

        # ── 11. Related tours ──────────────────────────
        # NOTE: Tour has no related_tours field (self-referential M2M) yet —
        # this key in the JSON is currently a no-op. Destination, TrekGuide
        # and BlogArticle all DO support related_tours pointing at Tour; only
        # tour-to-tour cross-linking needs a model field that doesn't exist.
        related_slugs = data.get('related_tours', [])
        if related_slugs:
            warnings.append(
                f"related_tours ignored: Tour has no related_tours field yet "
                f"— add a self-referential ManyToManyField to support this "
                f"({', '.join(related_slugs)})"
            )

        return {'created': created, 'slug': slug}

    @staticmethod
    def export_to_dict(tour) -> dict:
        """
        Export a Tour instance back to the JSON import format.
        Useful for round-tripping and backup.
        """
        from django.utils.text import slugify

        data = {
            "title": tour.title,
            "slug": tour.slug,
            "category": tour.category.name if tour.category else "",
            "tour_type": tour.tour_type,
            "place_name": tour.place_name,
            "duration_days": tour.duration_days,
            "difficulty": tour.difficulty,
            "price_usd": float(tour.price_usd),
            "excerpt": tour.excerpt,
            "description": tour.description,
            "target_audience": tour.target_audience,
            "lodge_level": tour.lodge_level,
            "beach_type": tour.beach_type,
            "image_alt_text": tour.image_alt_text,
            "is_active": tour.is_active,
            "is_featured": tour.is_featured,
            "tags": [t.slug for t in tour.tags.all()],
            "seo": {
                "meta_title": tour.meta_title,
                "meta_description": tour.meta_description,
                "focus_keyword": tour.focus_keyword,
                "secondary_keywords": tour.secondary_keywords,
                "canonical_url": tour.canonical_url,
                "schema_type": tour.schema_type,
                "og_title": tour.og_title,
                "og_description": tour.og_description,
                "twitter_card_type": tour.twitter_card_type,
                "seo_priority": tour.seo_priority,
                "structured_data": tour.structured_data,
            },
            "inclusions": [inc.name for inc in tour.inclusions.all()],
            "exclusions": [exc.name for exc in tour.exclusions.all()],
        }

        if tour.itinerary:
            data["itinerary"] = {
                "name": tour.itinerary.name,
                "description": tour.itinerary.description,
                "items": [
                    {
                        "day_number": item.day_number,
                        "title": item.title,
                        "description": item.description,
                        "time": item.time,
                        "tags": [t.slug for t in item.tags.all()],
                    }
                    for item in tour.itinerary.items.all().order_by("order")
                ],
            }

        # Content blocks
        data["content_blocks"] = [
            {
                "type": block.block_type,
                "heading": block.heading,
                "content": block.content,
                "order": block.order,
                "include_in_toc": block.include_in_toc,
                "focus_keyword": block.focus_keyword,
            }
            for block in tour.content_blocks.all().order_by("order")
        ]

        # Seasonal
        data["seasonal_windows"] = [
            {
                "month_start": w.month_start,
                "month_end": w.month_end,
                "rating": w.rating,
                "notes": w.notes,
            }
            for w in tour.seasonal_windows.all()
        ]

        # Gallery
        data["gallery"] = [
            {
                "cloudinary_url": str(img.image),
                "alt_text": img.alt_text,
                "order": img.order,
            }
            for img in tour.gallery.all().order_by("order")
        ]

        return data
