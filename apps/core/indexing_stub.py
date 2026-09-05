# apps/core/indexing_stub.py
#
# Stub that replaces apps.indexing when the indexing app is not installed.
# Provides the same interface so admin files import cleanly.
# When GOOGLE_INDEXING_ENABLED=1, swap this out for the real implementation.

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def should_auto_index() -> bool:
    return (
        getattr(settings, 'GOOGLE_INDEXING_ENABLED', False)
        and getattr(settings, 'GOOGLE_INDEXING_AUTO_ENABLED', False)
    )


def ping_google_and_update(instance, url, notification_type='URL_UPDATED'):
    """No-op stub. Returns False (not submitted). Enable indexing app to activate."""
    logger.debug("Google Indexing stub: skipping ping for %s (indexing not enabled)", url)
    return False


def submit_url_for_indexing(url, notification_type='URL_UPDATED'):
    logger.debug("Google Indexing stub: skipping %s", url)
    return False


def inspect_url(url):
    return {}


def submit_and_inspect(url):
    return {}


def bulk_submit_urls(urls, notification_type='URL_UPDATED'):
    return 0


def get_indexing_status_info():
    return {
        'enabled': False,
        'auto_enabled': False,
        'daily_quota': getattr(settings, 'GOOGLE_INDEXING_DAILY_QUOTA', 200),
        'note': 'Indexing app not installed. Set GOOGLE_INDEXING_ENABLED=1 and add apps.indexing to INSTALLED_APPS to activate.',
    }


# ── Admin mixin ───────────────────────────────────────────────────────────────

class GoogleIndexingActionMixin:
    """
    Stub mixin. When the real apps.indexing app is added back, replace this
    import in admin files:
        from apps.core.indexing_stub import GoogleIndexingActionMixin
    with:
        from apps.indexing.admin_mixins import GoogleIndexingActionMixin
    """
    pass
