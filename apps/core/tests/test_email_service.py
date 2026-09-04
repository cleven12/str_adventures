"""
CI-safe email tests using Django's locmem backend (no real SMTP).
"""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.core.services.email_service import EmailService


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='VISIT KILI ADVENTURES <noreply@example.com>',
    CONTACT_EMAIL='ops@example.com',
    STAFF_EMAILS=['ops@example.com', 'director@example.com'],
    SITE_NAME='VISIT KILI ADVENTURES',
    SITE_DOMAIN='v2.visitkili.com',
    WHATSAPP_NUMBER='+255741788255',
)
class EmailServiceTests(TestCase):
    def setUp(self):
        mail.outbox.clear()
        self.tour = SimpleNamespace(
            title='CI Test Safari',
            slug='ci-test-safari',
        )

    def test_staff_recipients_dedupes(self):
        with self.settings(STAFF_EMAILS=['a@x.com', 'a@x.com', 'b@x.com']):
            self.assertEqual(
                EmailService.staff_recipients(),
                ['a@x.com', 'b@x.com'],
            )

    def test_send_email_html_to_list(self):
        ok = EmailService.send_email(
            subject='CI unit mail',
            template_name='emails/contact_confirmation_user.html',
            context={
                'contact_message': {
                    'name': 'Tester',
                    'email': 'guest@example.com',
                    'phone': '',
                    'subject': 'Hi',
                    'message': 'Body',
                    'date_from': '',
                    'date_to': '',
                    'group_size': '',
                    'created_at': timezone.now(),
                }
            },
            to_email=['ops@example.com', 'director@example.com'],
        )
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            set(mail.outbox[0].to),
            {'ops@example.com', 'director@example.com'},
        )
        self.assertIn('CI unit mail', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].content_subtype, 'html')

    def test_send_email_rejects_empty_recipients(self):
        ok = EmailService.send_email(
            subject='Nope',
            template_name='emails/contact_confirmation_user.html',
            context={
                'contact_message': {
                    'name': 'X',
                    'email': 'x@x.com',
                    'phone': '',
                    'subject': '',
                    'message': 'm',
                    'date_from': '',
                    'date_to': '',
                    'group_size': '',
                    'created_at': timezone.now(),
                }
            },
            to_email=[],
        )
        self.assertFalse(ok)
        self.assertEqual(len(mail.outbox), 0)

    def test_contact_confirmation_notifies_staff_only(self):
        ok = EmailService.send_contact_confirmation(
            name='Guest',
            email='guest@example.com',
            subject='Climb dates',
            message='Looking for July trek',
            phone='+255700000000',
        )
        self.assertTrue(ok)
        # Staff only — no auto-confirmation to the visitor
        self.assertEqual(len(mail.outbox), 1)
        staff_msg = mail.outbox[0]
        self.assertIn('New Website Inquiry', staff_msg.subject)
        self.assertEqual(set(staff_msg.to), {'ops@example.com', 'director@example.com'})
        self.assertEqual(staff_msg.reply_to, ['guest@example.com'])

    def test_booking_received_sends_user_and_staff(self):
        booking = SimpleNamespace(
            email='guest@example.com',
            full_name='Guest User',
            phone_number='+255700000000',
            tour=self.tour,
            travel_date=date.today() + timedelta(days=40),
            num_people=2,
            preferred_contact='email',
            country='TZ',
            message='CI booking',
        )
        ok = EmailService.send_booking_received(booking)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ['guest@example.com'])
        self.assertEqual(set(mail.outbox[1].to), {'ops@example.com', 'director@example.com'})

    def test_payment_success_sends_user_and_staff(self):
        booking = SimpleNamespace(
            email='guest@example.com',
            booking_id='BKCI001',
            payment_amount=Decimal('500.00'),
            payment_confirmation_code='CONF',
            payment_method_used='Card',
            payment_date=timezone.now(),
            tour=self.tour,
        )
        ok = EmailService.send_payment_success(booking)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Payment Confirmed', mail.outbox[0].subject)
        self.assertIn('Payment Received', mail.outbox[1].subject)

    def test_payment_failed_sends_user_only(self):
        booking = SimpleNamespace(
            email='guest@example.com',
            booking_id='BKCI002',
            payment_amount=Decimal('500.00'),
            tour=self.tour,
        )
        ok = EmailService.send_payment_failed(booking, error_message='Declined')
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['guest@example.com'])
        self.assertIn('Payment Unsuccessful', mail.outbox[0].subject)

    def test_group_membership_received(self):
        group = SimpleNamespace(
            title='Group CI',
            slug='group-ci',
            tour=self.tour,
            start_date=timezone.now() + timedelta(days=50),
        )
        member = SimpleNamespace(
            email='guest@example.com',
            full_name='Guest',
            phone_number='+255700000000',
            group=group,
            party_size=2,
            country='US',
            message='join',
        )
        ok = EmailService.send_group_membership_received(member)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 2)
