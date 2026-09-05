# apps/guide/apps.py
# Co-authored-by: Neema <248148851+vwcwa-hue@users.noreply.github.com>
from django.apps import AppConfig

class GuideConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.guide'
    verbose_name = 'Guide'

    def ready(self):
        import apps.guide.signals  # noqa
