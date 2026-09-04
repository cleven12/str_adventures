"""
Email staff a post-deploy / CI notification (uses live SMTP from .env).

  python manage.py notify_deploy --status success --sha abc123 --ref main
  python manage.py notify_deploy --status failed --message "migrate error"
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Notify STAFF_EMAILS about a deploy or CI result."

    def add_arguments(self, parser):
        parser.add_argument('--status', choices=['success', 'failed', 'info'], default='info')
        parser.add_argument('--sha', default='')
        parser.add_argument('--ref', default='')
        parser.add_argument('--message', default='')
        parser.add_argument('--site-url', default='')
        parser.add_argument(
            '--to',
            default='',
            help='Comma-separated override recipients (default STAFF_EMAILS)',
        )

    def handle(self, *args, **options):
        if options['to']:
            recipients = [e.strip() for e in options['to'].split(',') if e.strip()]
        else:
            recipients = list(settings.STAFF_EMAILS) or [settings.CONTACT_EMAIL]
        recipients = [r for r in recipients if r]
        if not recipients:
            raise CommandError('No recipients configured')

        status = options['status']
        site = (options['site_url'] or f"https://{settings.SITE_DOMAIN}").rstrip('/')
        now = timezone.localtime().strftime('%Y-%m-%d %H:%M %Z')
        icon = {'success': '✅', 'failed': '❌', 'info': 'ℹ️'}.get(status, 'ℹ️')

        subject = f"[{settings.SITE_NAME}] {icon} Deploy {status.upper()} — {settings.SITE_DOMAIN}"
        body = (
            f"Visit Kili deploy notification\n"
            f"{'=' * 40}\n"
            f"Status : {status}\n"
            f"Time   : {now}\n"
            f"Site   : {site}\n"
            f"Domain : {settings.SITE_DOMAIN}\n"
            f"Ref    : {options['ref'] or '(n/a)'}\n"
            f"SHA    : {options['sha'] or '(n/a)'}\n"
            f"Message: {options['message'] or '(none)'}\n"
            f"\n"
            f"Quick checks:\n"
            f"  Home     {site}/\n"
            f"  Robots   {site}/robots.txt\n"
            f"  Sitemap  {site}/sitemap.xml\n"
            f"  Contact  {site}/contact/\n"
            f"  DPO IPN  {site}/booking/dpo/callback/\n"
            f"\n"
            f"Server logs: /var/www/visit_kili/logs/\n"
            f"  django.log | payment.log | mail.log | error.log\n"
        )

        try:
            sent = send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f'Failed to send deploy notification: {exc}') from exc

        if not sent:
            raise CommandError('send_mail returned 0')

        self.stdout.write(self.style.SUCCESS(f'Notified {recipients} ({status})'))
