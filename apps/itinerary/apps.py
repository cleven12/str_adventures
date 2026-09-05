# apps/itinerary/apps.py
from django.apps import AppConfig

class ItineraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.itinerary'
    verbose_name = 'Itinerary'

    def ready(self):
        pass
        # import apps.itinerary.signals  # noqa