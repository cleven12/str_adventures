# apps/tours/signals.py
# Auto-ping Google Indexing API when a tour or combo goes live or is updated.
# Uses stub when apps.indexing is not installed — safe no-op.

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


def _should_ping() -> bool:
    return (
        getattr(settings, 'GOOGLE_INDEXING_ENABLED', False)
        and getattr(settings, 'GOOGLE_INDEXING_AUTO_ENABLED', False)
    )


def _ping_async(func, *args, **kwargs):
    import threading
    t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    t.start()


@receiver(post_save, sender='tours.Tour')
def handle_tour_indexing(sender, instance, created, **kwargs):
    if instance.is_active and _should_ping():
        try:
            from apps.core.indexing_stub import ping_google_and_update
            domain = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
            url = f"https://{domain}{instance.get_absolute_url()}"
            _ping_async(ping_google_and_update, instance, url, 'URL_UPDATED')
        except Exception as e:
            logger.error("Tour Google indexing signal error: %s", e)


@receiver(post_save, sender='tours.ComboPackage')
def handle_combo_indexing(sender, instance, created, **kwargs):
    if not instance.is_active:
        return
    if _should_ping():
        try:
            from apps.core.indexing_stub import ping_google_and_update
            domain = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
            url = f"https://{domain}{instance.get_absolute_url()}"
            _ping_async(ping_google_and_update, instance, url, 'URL_UPDATED')
        except Exception as e:
            logger.error("Combo Google indexing signal error: %s", e)
