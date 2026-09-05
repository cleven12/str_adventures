# apps/core/management/commands/seo_engine.py
# SEO Engine management command — schema generation only.
# Google Indexing API calls are stubbed; enable apps.indexing to activate.

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "SEO Engine: schema validation and Google indexing status"

    def add_arguments(self, parser):
        parser.add_argument('--status', action='store_true', help='Show indexing status')
        parser.add_argument('--ping', metavar='URL', help='Ping Google for a single URL')

    def handle(self, *args, **options):
        if options.get('status'):
            from apps.core.indexing_stub import get_indexing_status_info
            info = get_indexing_status_info()
            for k, v in info.items():
                self.stdout.write(f"  {k}: {v}")
            return

        if options.get('ping'):
            from apps.core.indexing_stub import submit_url_for_indexing
            url = options['ping']
            ok = submit_url_for_indexing(url)
            self.stdout.write(f"{'OK' if ok else 'STUB (no-op)'}: {url}")
            return

        self.stdout.write("SEO Engine ready. Use --status or --ping <url>.")
