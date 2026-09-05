# apps/booking/api_views.py
# Write endpoints for booking enquiries, group-join requests and contact.

import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tours.models import Tour
from apps.core.services.email_service import EmailService
from .models import Booking, GroupDeparture, GroupMember, ContactEnquiry
from .forms import BookingForm, GroupJoinForm, ContactEnquiryForm

logger = logging.getLogger(__name__)


def _send_booking_emails(booking):
    try:
        EmailService.send_booking_received(booking)
    except Exception:
        logger.exception("Failed to send booking emails for %s", booking.booking_ref)


def _send_group_join_emails(member):
    try:
        EmailService.send_group_join_received(member)
    except Exception:
        logger.exception("Failed to send group join emails for %s", member.member_id)


# ══════════════════════════════════════════════════════════════════════════════
# BOOKINGS
# ══════════════════════════════════════════════════════════════════════════════

class BookingCreateView(APIView):
    """POST /api/v1/bookings/ — {tour_slug, ...BookingForm fields}"""

    def post(self, request):
        tour_slug = (request.data.get("tour_slug") or "").strip()
        tour = get_object_or_404(Tour, slug=tour_slug, is_active=True)

        form = BookingForm(request.data)
        if not form.is_valid():
            return Response({"errors": form.errors}, status=400)

        try:
            with transaction.atomic():
                booking = form.save(commit=False)
                booking.tour = tour
                booking.save()
                transaction.on_commit(lambda b=booking: _send_booking_emails(b))
        except Exception:
            logger.exception("Booking save failed for tour %s", tour_slug)
            return Response(
                {"detail": "Something went wrong saving your request. Please try again."},
                status=500,
            )

        return Response(
            {
                "booking_ref":  booking.booking_ref,
                "secure_token": booking.secure_token,
                "tour":         {"slug": tour.slug, "title": tour.title},
            },
            status=201,
        )


class BookingStatusView(APIView):
    """GET /api/v1/bookings/<booking_ref>/<secure_token>/"""

    def get(self, request, booking_ref, secure_token):
        booking = get_object_or_404(
            Booking.objects.select_related("tour"),
            booking_ref=booking_ref, secure_token=secure_token,
        )
        return Response({
            "booking_ref":       booking.booking_ref,
            "status":            booking.status,
            "tour":              {"slug": booking.tour.slug, "title": booking.tour.title},
            "full_name":         booking.full_name,
            "num_people":        booking.num_people,
            "travel_date":       booking.travel_date,
            "quoted_price_usd":  booking.quoted_price_usd,
            "dpo_payment_url":   booking.dpo_payment_url if booking.dpo_payment_url_sent else None,
            "payment_confirmed": booking.payment_confirmed,
            "created_at":        booking.created_at,
        })


class BookingCancelView(APIView):
    """POST /api/v1/bookings/<booking_ref>/<secure_token>/cancel/"""

    def post(self, request, booking_ref, secure_token):
        booking = get_object_or_404(
            Booking, booking_ref=booking_ref, secure_token=secure_token
        )
        if booking.status in ("confirmed", "completed"):
            return Response(
                {
                    "status": booking.status,
                    "detail": "This booking is already confirmed — please contact us "
                              "directly to discuss a cancellation.",
                },
                status=409,
            )
        booking.status = "cancelled"
        booking.save(update_fields=["status", "updated_at"])
        return Response({
            "status": booking.status,
            "detail": "Your booking request has been cancelled.",
        })


# ══════════════════════════════════════════════════════════════════════════════
# GROUP DEPARTURES — join requests
# ══════════════════════════════════════════════════════════════════════════════

class GroupJoinView(APIView):
    """POST /api/v1/group-departures/<slug>/join/"""

    def post(self, request, slug):
        group = get_object_or_404(GroupDeparture, slug=slug, is_active=True)

        form = GroupJoinForm(request.data)
        if not form.is_valid():
            return Response({"errors": form.errors}, status=400)

        try:
            with transaction.atomic():
                locked_group = GroupDeparture.objects.select_for_update().get(pk=group.pk)

                if not locked_group.is_accepting_requests:
                    return Response(
                        {"detail": "Sorry, this group is no longer accepting new requests."},
                        status=409,
                    )

                member = form.save(commit=False)
                member.group = locked_group

                if locked_group.spots_remaining < member.party_size:
                    return Response(
                        {
                            "detail": (
                                f"Only {locked_group.spots_remaining} spot"
                                f"{'s' if locked_group.spots_remaining != 1 else ''} remaining. "
                                "Please reduce your party size or contact us."
                            )
                        },
                        status=409,
                    )

                member.save()
                transaction.on_commit(lambda m=member: _send_group_join_emails(m))
        except Exception:
            logger.exception("Group join failed for group %s", slug)
            return Response(
                {"detail": "Something went wrong saving your request. Please try again."},
                status=500,
            )

        return Response(
            {"member_id": member.member_id, "secure_token": member.secure_token},
            status=201,
        )


class GroupJoinStatusView(APIView):
    """GET /api/v1/group-departures/join/<member_id>/<secure_token>/"""

    def get(self, request, member_id, secure_token):
        member = get_object_or_404(
            GroupMember.objects.select_related("group__tour"),
            member_id=member_id, secure_token=secure_token,
        )
        return Response({
            "member_id":   member.member_id,
            "status":      member.status,
            "party_size":  member.party_size,
            "group": {
                "slug":       member.group.slug,
                "title":      member.group.title,
                "start_date": member.group.start_date,
            },
            "tour": {"slug": member.group.tour.slug, "title": member.group.tour.title},
        })


# ══════════════════════════════════════════════════════════════════════════════
# CONTACT
# ══════════════════════════════════════════════════════════════════════════════

class ContactCreateView(APIView):
    """POST /api/v1/contact/"""

    def post(self, request):
        form = ContactEnquiryForm(request.data)
        if not form.is_valid():
            return Response({"errors": form.errors}, status=400)

        try:
            with transaction.atomic():
                enquiry = form.save()
                transaction.on_commit(
                    lambda e=enquiry: EmailService.send_contact_notification(e)
                )
        except Exception:
            logger.exception("Contact form save failed")
            return Response(
                {"detail": "Something went wrong. Please try again."}, status=500
            )

        return Response(
            {"detail": "Message sent! We'll be in touch within 24 hours."}, status=201
        )
