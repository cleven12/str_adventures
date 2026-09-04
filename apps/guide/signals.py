# apps/guide/signals.py
# Auto-ping Google Indexing API on guide/article publish.

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


def _should_ping():
    return (
        getattr(settings, 'GOOGLE_INDEXING_ENABLED', False)
        and getattr(settings, 'GOOGLE_INDEXING_AUTO_ENABLED', False)
    )


def _ping_async(func, *args, **kwargs):
    import threading
    t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    t.start()


@receiver(post_save, sender='guide.TrekGuide')
def handle_guide_indexing(sender, instance, **kwargs):
    if instance.is_published and _should_ping():
        try:
            from apps.core.indexing_stub import ping_google_and_update
            domain = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
            url = f"https://{domain}{instance.get_absolute_url()}"
            _ping_async(ping_google_and_update, instance, url, 'URL_UPDATED')
        except Exception as e:
            logger.error("Guide Google indexing signal error: %s", e)


@receiver(post_save, sender='guide.BlogArticle')
def handle_article_indexing(sender, instance, **kwargs):
    if instance.status == 'published' and _should_ping():
        try:
            from apps.core.indexing_stub import ping_google_and_update
            domain = getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')
            url = f"https://{domain}{instance.get_absolute_url()}"
            _ping_async(ping_google_and_update, instance, url, 'URL_UPDATED')
        except Exception as e:
            logger.error("Article Google indexing signal error: %s", e)
