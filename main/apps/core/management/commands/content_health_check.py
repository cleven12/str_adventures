"""
Command to run various health checks on content for SEO and data quality.

Pure code addition for operational tooling.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = "Run health checks on tours, destinations, etc."

    def handle(self, *args, **options):
        self.stdout.write("Running content health checks...\n")

        from apps.tours.models import Tour
        bad_tours = Tour.objects.filter(
            Q(focus_keyword="") | Q(meta_title="") | Q(price_usd__lt=1)
        ).count()

        self.stdout.write(f"Tours with incomplete SEO or bad pricing: {bad_tours}")

        from apps.destinations.models import Destination
        bad_dests = Destination.objects.filter(focus_keyword="").count()
        self.stdout.write(f"Destinations missing focus keyword: {bad_dests}")

        self.stdout.write(self.style.SUCCESS("\nHealth check complete."))
