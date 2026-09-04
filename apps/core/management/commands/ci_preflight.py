"""
CI / pre-deploy preflight checks (no external network required).

  python manage.py ci_preflight
  python manage.py ci_preflight --strict
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse


class Command(BaseCommand):
    help = "Run SEO + mail-config + route preflight checks for CI."

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Fail if EMAIL_HOST_USER is empty (staging/prod expectation).',
        )

    def handle(self, *args, **options):
        errors = []
        warnings = []

        self.stdout.write(self.style.MIGRATE_HEADING('CI preflight'))

        # --- Mail config ---
        backend = getattr(settings, 'EMAIL_BACKEND', '')
        host_user = getattr(settings, 'EMAIL_HOST_USER', '') or ''
        self.stdout.write(f'  EMAIL_BACKEND   = {backend}')
        self.stdout.write(f'  EMAIL_HOST_USER = {host_user or "(empty)"}')
        self.stdout.write(f'  DEFAULT_FROM    = {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'  STAFF_EMAILS    = {list(settings.STAFF_EMAILS)}')
        self.stdout.write(f'  SITE_DOMAIN     = {settings.SITE_DOMAIN}')

        if options['strict'] and not host_user:
            errors.append('EMAIL_HOST_USER empty while --strict (SMTP not configured)')

        if not list(settings.STAFF_EMAILS):
            warnings.append('STAFF_EMAILS is empty — staff will not get ops mail')

        if 'console' in backend and options['strict']:
            warnings.append('Using console email backend in strict mode')

        # --- Public SEO routes ---
        client = Client()
        checks = [
            ('home', reverse('core:home')),
            ('robots', reverse('core:robots')),
            ('sitemap', '/sitemap.xml'),
            ('contact', reverse('core:contact')),
            ('tours', reverse('tours:tour_list')),
            ('destinations', reverse('destinations:list')),
            ('guides', reverse('guide:guide_list')),
            ('dpo_callback_method', '/booking/dpo/callback/'),
        ]
        for name, path in checks:
            if name == 'dpo_callback_method':
                resp = client.get(path)
                # POST-only endpoint should not 500 on GET
                if resp.status_code >= 500:
                    errors.append(f'{name} GET returned {resp.status_code}')
                else:
                    self.stdout.write(self.style.SUCCESS(f'  OK  {name} ({resp.status_code}) {path}'))
                continue

            resp = client.get(path)
            if resp.status_code != 200:
                errors.append(f'{name} returned {resp.status_code} for {path}')
            else:
                self.stdout.write(self.style.SUCCESS(f'  OK  {name} (200) {path}'))

        # robots/sitemap content snippets
        robots = client.get(reverse('core:robots'))
        if robots.status_code == 200 and b'Sitemap:' not in robots.content:
            errors.append('robots.txt missing Sitemap: line')

        sitemap = client.get('/sitemap.xml')
        if sitemap.status_code == 200 and b'<urlset' not in sitemap.content:
            errors.append('sitemap.xml missing <urlset>')

        # --- Optional content SEO stats (soft) ---
        try:
            from apps.tours.models import Tour
            from apps.destinations.models import Destination

            tours = Tour.objects.filter(is_active=True)
            missing_tour_seo = tours.filter(focus_keyword='').count() + tours.filter(meta_title='').count()
            dest_missing = Destination.objects.filter(is_active=True, focus_keyword='').count() if hasattr(Destination, 'focus_keyword') else 0
            self.stdout.write(f'  Active tours: {tours.count()} (SEO field gaps count≈{missing_tour_seo})')
            if dest_missing:
                warnings.append(f'{dest_missing} active destinations missing focus_keyword')
            if missing_tour_seo:
                warnings.append(f'Tour SEO gaps detected (≈{missing_tour_seo} empty fields)')
        except Exception as exc:
            warnings.append(f'Content SEO stats skipped: {exc}')

        for w in warnings:
            self.stdout.write(self.style.WARNING(f'  WARN  {w}'))

        if errors:
            for e in errors:
                self.stdout.write(self.style.ERROR(f'  FAIL  {e}'))
            raise CommandError(f'Preflight failed with {len(errors)} error(s)')

        self.stdout.write(self.style.SUCCESS('\nPreflight passed.'))
