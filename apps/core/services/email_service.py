# apps/core/services/email_service.py
# Structured Adventures — email service
#
# Design:
#   • Every email is purely informational — no payment links generated here.
#   • Staff emails always include a direct Django admin link to the record.
#   • Client emails are warm, branded, and set expectations clearly.
#   • reply_to on staff emails = client's email so staff can reply directly.
#   • All methods return True/False, never raise — callers don't need to handle errors.

import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


class EmailService:

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _staff_recipients():
        """Return deduplicated list of staff email addresses."""
        emails = [
            e.strip()
            for e in list(getattr(settings, 'STAFF_EMAILS', []) or [])
            if e and str(e).strip()
        ]
        if not emails and getattr(settings, 'CONTACT_EMAIL', None):
            emails = [settings.CONTACT_EMAIL]
        seen, out = set(), []
        for e in emails:
            key = e.lower()
            if key not in seen:
                seen.add(key)
                out.append(e)
        return out

    @staticmethod
    def _base_context():
        """Context vars available in every email template."""
        return {
            'SITE_NAME':       getattr(settings, 'SITE_NAME', 'Structured Adventures'),
            'SITE_DOMAIN':     getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com'),
            'WHATSAPP_NUMBER': getattr(settings, 'WHATSAPP_NUMBER', ''),
            'site_url':        f"https://{getattr(settings, 'SITE_DOMAIN', 'structuredadventures.com')}",
        }

    @classmethod
    def _send(cls, *, subject, template, context, to, reply_to=None):
        """
        Core send method. Returns True on success.
        Never raises — errors are logged.
        """
        try:
            recipients = [to] if isinstance(to, str) else list(to or [])
            recipients = [r.strip() for r in recipients if r and str(r).strip()]
            if not recipients:
                logger.error("Email skipped — no recipients for subject=%r", subject)
                return False

            ctx = {**cls._base_context(), **context}
            html = render_to_string(template, ctx)

            msg = EmailMessage(
                subject=f"[{ctx['SITE_NAME']}] {subject}",
                body=html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
                reply_to=[reply_to] if reply_to else None,
            )
            msg.content_subtype = 'html'
            msg.send(fail_silently=False)
            logger.info("Email sent subject=%r to=%s", subject, recipients)
            return True
        except Exception:
            logger.exception("Email failed subject=%r to=%s", subject, to)
            return False

    @staticmethod
    def _admin_url(obj):
        """Build Django admin change URL for a model instance."""
        try:
            app  = obj._meta.app_label
            name = obj._meta.model_name
            return (
                f"https://{getattr(settings, 'SITE_DOMAIN', '')}"
                f"/admin/{app}/{name}/{obj.pk}/change/"
            )
        except Exception:
            return ''

    # ── Booking emails ─────────────────────────────────────────────────────────

    @classmethod
    def send_booking_received(cls, booking):
        """
        Fire two emails:
        1. Client — confirmation that their request was received.
        2. Staff  — actionable notification with admin link to review.
        Returns True if client email succeeded.
        """
        context = {
            'booking':    booking,
            'tour':       booking.tour,
            'admin_url':  cls._admin_url(booking),
        }

        # Client email
        client_ok = False
        if booking.email:
            client_ok = cls._send(
                subject=f"Your Adventure Enquiry — {booking.booking_ref}",
                template='emails/booking_received_client.html',
                context=context,
                to=booking.email,
            )

        # Staff email — always send, reply-to = client
        cls._send(
            subject=(
                f"New Booking Request: {booking.tour.title} "
                f"— {booking.full_name} [{booking.booking_ref}]"
            ),
            template='emails/booking_received_staff.html',
            context=context,
            to=cls._staff_recipients(),
            reply_to=booking.email or None,
        )

        return client_ok

    @classmethod
    def send_booking_confirmed(cls, booking):
        """
        Notify client that their booking is confirmed and staff are in touch.
        Staff do NOT get a separate email here — they triggered the action.
        """
        if not booking.email:
            return False
        return cls._send(
            subject=f"Booking Confirmed — {booking.booking_ref}",
            template='emails/booking_confirmed_client.html',
            context={'booking': booking, 'tour': booking.tour},
            to=booking.email,
        )

    @classmethod
    def send_dpo_link_notification(cls, booking):
        """
        Notify client that their DPO payment link is ready.
        Staff use this after pasting the DPO URL into the booking record.
        Called from the admin action, not from any public view.
        """
        if not booking.email or not booking.dpo_payment_url:
            logger.warning(
                "Cannot send DPO link — missing email or URL for booking %s",
                booking.booking_ref,
            )
            return False
        return cls._send(
            subject=f"Your Payment Link — {booking.booking_ref}",
            template='emails/booking_dpo_link.html',
            context={
                'booking':         booking,
                'tour':            booking.tour,
                'dpo_payment_url': booking.dpo_payment_url,
                'quoted_price':    booking.quoted_price_usd,
            },
            to=booking.email,
        )

    # ── Group departure emails ──────────────────────────────────────────────────

    @classmethod
    def send_group_join_received(cls, member):
        """
        Fire after a group join request is saved.
        Client gets a 'we received your request' email.
        Staff get an actionable notification.
        """
        context = {
            'member':    member,
            'group':     member.group,
            'tour':      member.group.tour,
            'admin_url': cls._admin_url(member),
        }

        client_ok = cls._send(
            subject=f"Group Join Request Received — {member.member_id}",
            template='emails/group_join_received_client.html',
            context=context,
            to=member.email,
        )
        cls._send(
            subject=(
                f"New Group Join: {member.group.title} "
                f"— {member.full_name} ({member.party_size} pax) [{member.member_id}]"
            ),
            template='emails/group_join_received_staff.html',
            context=context,
            to=cls._staff_recipients(),
            reply_to=member.email,
        )
        return client_ok

    @classmethod
    def send_group_member_accepted(cls, member):
        """
        Notify client that their join request has been accepted.
        Tells them to expect a payment link via WhatsApp/email from staff.
        """
        return cls._send(
            subject=f"Your Spot is Reserved — {member.group.title}",
            template='emails/group_join_accepted_client.html',
            context={
                'member': member,
                'group':  member.group,
                'tour':   member.group.tour,
            },
            to=member.email,
        )

    @classmethod
    def send_group_dpo_link_notification(cls, member):
        """
        Notify client that their DPO payment link has been sent.
        Called from admin action after staff paste the link.
        """
        if not member.email or not member.dpo_payment_url:
            return False
        return cls._send(
            subject=f"Payment Link for {member.group.title} — {member.member_id}",
            template='emails/group_dpo_link.html',
            context={
                'member':          member,
                'group':           member.group,
                'tour':            member.group.tour,
                'dpo_payment_url': member.dpo_payment_url,
            },
            to=member.email,
        )

    # ── Contact enquiry emails ──────────────────────────────────────────────────

    @classmethod
    def send_contact_notification(cls, enquiry):
        """
        Staff notification of a new contact form submission.
        reply-to = enquirer so staff can reply directly from their inbox.
        """
        cls._send(
            subject=f"New Enquiry: {enquiry.subject} — {enquiry.name}",
            template='emails/contact_staff.html',
            context={'enquiry': enquiry, 'admin_url': cls._admin_url(enquiry)},
            to=cls._staff_recipients(),
            reply_to=enquiry.email,
        )
        # Optional: auto-confirm to client
        cls._send(
            subject="We received your message — Structured Adventures",
            template='emails/contact_received_client.html',
            context={'enquiry': enquiry},
            to=enquiry.email,
        )

    # ── Job application ────────────────────────────────────────────────────────

    @classmethod
    def send_job_application(cls, application, cv_file=None):
        """
        Staff notification with optional CV attachment.
        cv_file: in-memory UploadedFile from request.FILES.
        """
        try:
            recipients = cls._staff_recipients()
            if not recipients:
                return False

            ctx = {
                **cls._base_context(),
                'application': application,
                'admin_url':   cls._admin_url(application),
            }
            html = render_to_string('emails/job_application_staff.html', ctx)

            msg = EmailMessage(
                subject=f"[{ctx['SITE_NAME']}] New Application: {application.job.title} — {application.name}",
                body=html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
                reply_to=[application.email],
            )
            msg.content_subtype = 'html'

            if cv_file is not None:
                cv_file.seek(0)
                msg.attach(cv_file.name, cv_file.read(), cv_file.content_type)

            msg.send(fail_silently=False)
            return True
        except Exception:
            logger.exception("Job application email failed for application %s", application.pk)
            return False
