from django.apps import AppConfig


class DestinationsConfig(AppConfig):
    name = 'apps.destinations'

    def ready(self):
        # Wire Google self-indexing for destinations (seo-destination skill output)
        import apps.destinations.signals  # noqa
