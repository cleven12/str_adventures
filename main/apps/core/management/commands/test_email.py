"""
Verify SMTP connectivity and send a test message.

Usage:
  python manage.py test_email
  python manage.py test_email --to you@example.com
  python manage.py test_email --dry-run   # only print config / open connection
"""
from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Test Django email / SMTP configuration (connection + optional send)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default='',
            help='Recipient for the test message (default: first STAFF_EMAILS / CONTACT_EMAIL)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only validate settings and open SMTP connection; do not send mail',
        )

    def handle(self, *args, **options):
        backend = settings.EMAIL_BACKEND
        host_user = getattr(settings, 'EMAIL_HOST_USER', '') or ''
        host = getattr(settings, 'EMAIL_HOST', '') or ''
        port = getattr(settings, 'EMAIL_PORT', None)
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
        timeout = getattr(settings, 'EMAIL_TIMEOUT', None)
        from_email = settings.DEFAULT_FROM_EMAIL

        self.stdout.write(self.style.MIGRATE_HEADING('Email configuration'))
        self.stdout.write(f'  EMAIL_BACKEND     = {backend}')
        self.stdout.write(f'  EMAIL_HOST        = {host or "(none)"}')
        self.stdout.write(f'  EMAIL_PORT        = {port}')
        self.stdout.write(f'  EMAIL_USE_TLS     = {use_tls}')
        self.stdout.write(f'  EMAIL_USE_SSL     = {use_ssl}')
        self.stdout.write(f'  EMAIL_TIMEOUT     = {timeout}')
        self.stdout.write(f'  EMAIL_HOST_USER   = {host_user or "(empty — console fallback if unset)"}')
        self.stdout.write(f'  DEFAULT_FROM_EMAIL= {from_email}')
        self.stdout.write(f'  CONTACT_EMAIL     = {settings.CONTACT_EMAIL}')
        self.stdout.write(f'  STAFF_EMAILS      = {list(settings.STAFF_EMAILS)}')
        self.stdout.write(f'  SITE_DOMAIN       = {settings.SITE_DOMAIN}')

        if 'console' in backend:
            self.stdout.write(self.style.WARNING(
                '\nUsing console backend — emails are printed to stdout, not delivered.\n'
                'Set EMAIL_HOST_USER (+ host/password) in .env for real SMTP.'
            ))

        if host_user and 'gmail.com' in (host or 'smtp.gmail.com') and 'info@' in from_email.lower():
            self.stdout.write(self.style.WARNING(
                '\nNote: Gmail SMTP often rejects or rewrites From when DEFAULT_FROM_EMAIL\n'
                'is not the authenticated Gmail address (or a verified "Send mail as" alias).\n'
                f'Consider: DEFAULT_FROM_EMAIL="VISIT KILI ADVENTURES <{host_user}>"'
            ))

        self.stdout.write(self.style.MIGRATE_HEADING('\nOpening mail connection…'))
        try:
            conn = get_connection(fail_silently=False)
            conn.open()
            self.stdout.write(self.style.SUCCESS('  Connection OK'))
            conn.close()
        except Exception as exc:
            raise CommandError(f'SMTP connection failed: {exc}') from exc

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('\nDry run complete — no message sent.'))
            return

        to_raw = (options['to'] or '').strip()
        if to_raw:
            recipients = [e.strip() for e in to_raw.replace(';', ',').split(',') if e.strip()]
        else:
            staff = list(settings.STAFF_EMAILS)
            recipients = staff[:1] if staff else ([settings.CONTACT_EMAIL] if settings.CONTACT_EMAIL else [])
        if not recipients:
            raise CommandError('No recipient. Pass --to you@example.com (comma-separated OK)')

        subject = f'[{settings.SITE_NAME}] SMTP test'
        body = (
            f'This is a test email from VISIT KILI ADVENTURES.\n\n'
            f'Backend: {backend}\n'
            f'Host: {host}:{port}\n'
            f'From: {from_email}\n'
            f'Site: {settings.SITE_DOMAIN}\n'
        )

        self.stdout.write(f'\nSending test message to {", ".join(recipients)}…')
        try:
            sent = send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f'Send failed: {exc}') from exc

        if sent:
            self.stdout.write(self.style.SUCCESS(f'Sent successfully to {", ".join(recipients)}'))
        else:
            raise CommandError('send_mail returned 0 (message not sent)')
