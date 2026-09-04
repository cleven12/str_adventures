# apps/booking/views.py
# Structured Adventures — booking views
#
# Philosophy: the web does ONE thing — capture enquiries cleanly and notify staff.
# All payment happens offline via a DPO link staff generate and send manually.
# There are NO gateway API calls from any view in this file.

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_POST

from apps.tours.models import Tour
from .models import GroupDeparture, GroupMember, Booking, ContactEnquiry
from .forms import BookingForm, GroupJoinForm, ContactEnquiryForm
from apps.core.services.email_service import EmailService

logger = logging.getLogger(__name__)


def _save_last_url(request):
    request.session['last_url'] = request.path


# ==============================================================================
# INDIVIDUAL TOUR BOOKING
# ==============================================================================

def booking_create(request, tour_slug):
    """
    Step 1 of the booking process: capture client details.
    On POST — save to DB, email staff + client, redirect to confirmation page.
    No payment, no DPO calls.
    """
    _save_last_url(request)
    tour = get_object_or_404(Tour, slug=tour_slug, is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    booking = form.save(commit=False)
                    booking.tour = tour
                    booking.save()
                    # Emails fire after commit so a rollback won't send them
                    transaction.on_commit(lambda b=booking: _send_booking_emails(b))

                return redirect(
                    'booking:booking_received',
                    booking_ref=booking.booking_ref,
                    secure_token=booking.secure_token,
                )
            except Exception:
                logger.exception("Booking save failed for tour %s", tour_slug)
                messages.error(
                    request,
                    "Something went wrong saving your request. Please try again "
                    "or contact us directly on WhatsApp."
                )
        # Form invalid — fall through to re-render with errors
        if request.headers.get('HX-Request'):
            # Return just the form partial for HTMX inline replacement
            return render(request, 'booking/partials/booking_form.html', {
                'form': form, 'tour': tour
            })
    else:
        form = BookingForm(initial={'num_people': 1})

    return render(request, 'booking/booking_create.html', {
        'tour':  tour,
        'form':  form,
        'meta_title': f"Book {tour.title} | Structured Adventures",
    })


def booking_received(request, booking_ref, secure_token):
    """
    Confirmation page shown after a booking request is submitted.
    Authenticated by booking_ref + secure_token so the client can bookmark it.
    """
    booking = get_object_or_404(
        Booking, booking_ref=booking_ref, secure_token=secure_token
    )
    return render(request, 'booking/booking_received.html', {
        'booking': booking,
        'tour':    booking.tour,
        'meta_title': f"Request Received — {booking.booking_ref} | Structured Adventures",
    })


def booking_confirm(request, booking_ref, secure_token):
    """
    Status page the client can check at any time.
    Shows current status, whether DPO link has been sent, etc.
    No sensitive payment data here — just enquiry status.
    """
    booking = get_object_or_404(
        Booking, booking_ref=booking_ref, secure_token=secure_token
    )
    return render(request, 'booking/booking_status.html', {
        'booking': booking,
        'tour':    booking.tour,
        'meta_title': f"Booking Status — {booking.booking_ref} | Structured Adventures",
    })


def booking_cancel(request, booking_ref, secure_token):
    """Client-initiated cancellation (before payment)."""
    booking = get_object_or_404(
        Booking, booking_ref=booking_ref, secure_token=secure_token
    )
    if booking.status not in ('confirmed', 'completed'):
        booking.status = 'cancelled'
        booking.save(update_fields=['status', 'updated_at'])
        messages.info(request, "Your booking request has been cancelled.")
    else:
        messages.warning(
            request,
            "This booking is already confirmed — please contact us directly "
            "to discuss a cancellation."
        )
    return redirect('tours:tour_detail', slug=booking.tour.slug)


# ==============================================================================
# GROUP DEPARTURES
# ==============================================================================

def group_list(request):
    _save_last_url(request)
    groups = (
        GroupDeparture.objects
        .filter(is_active=True, start_date__gte=timezone.now())
        .select_related('tour')
        .order_by('start_date')
    )
    return render(request, 'booking/group_list.html', {
        'groups':           groups,
        'meta_title':       'Group Departures | Structured Adventures',
        'meta_description': (
            'Join a fixed-date group trek on Kilimanjaro or a shared safari. '
            'Clear pricing, expert guides, great company.'
        ),
    })


def group_detail(request, slug):
    _save_last_url(request)
    group = get_object_or_404(
        GroupDeparture.objects.select_related('tour'),
        slug=slug, is_active=True
    )
    form = GroupJoinForm()
    return render(request, 'booking/group_detail.html', {
        'group': group,
        'tour':  group.tour,
        'form':  form,
        'meta_title': f"{group.title} | Structured Adventures",
    })


def group_join(request, slug):
    """
    Process a join request for a group departure.
    Uses select_for_update to prevent overbooking.
    No DPO call — staff send the payment link manually after review.
    """
    group = get_object_or_404(GroupDeparture, slug=slug, is_active=True)

    if request.method != 'POST':
        return redirect('booking:group_detail', slug=slug)

    form = GroupJoinForm(request.POST)

    if not form.is_valid():
        if request.headers.get('HX-Request'):
            return _htmx_form_errors(form)
        messages.error(request, "Please correct the errors below.")
        return render(request, 'booking/group_detail.html', {
            'group': group, 'tour': group.tour, 'form': form
        })

    try:
        with transaction.atomic():
            locked_group = GroupDeparture.objects.select_for_update().get(pk=group.pk)

            if not locked_group.is_accepting_requests:
                msg = "Sorry, this group is no longer accepting new requests."
                if request.headers.get('HX-Request'):
                    return _htmx_error(msg)
                messages.warning(request, msg)
                return redirect('booking:group_detail', slug=slug)

            member = form.save(commit=False)
            member.group = locked_group

            if locked_group.spots_remaining < member.party_size:
                msg = (
                    f"Only {locked_group.spots_remaining} spot"
                    f"{'s' if locked_group.spots_remaining != 1 else ''} remaining. "
                    "Please reduce your party size or contact us."
                )
                if request.headers.get('HX-Request'):
                    return _htmx_error(msg)
                messages.warning(request, msg)
                return redirect('booking:group_detail', slug=slug)

            member.save()
            transaction.on_commit(lambda m=member: _send_group_join_emails(m))

        # Redirect to received page
        received_url = reverse(
            'booking:group_join_received',
            kwargs={'member_id': member.member_id, 'secure_token': member.secure_token}
        )
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = received_url
            return response
        return redirect(received_url)

    except Exception:
        logger.exception("Group join failed for group %s", slug)
        msg = (
            "Something went wrong saving your request. "
            "Please try again or contact us on WhatsApp."
        )
        if request.headers.get('HX-Request'):
            return _htmx_error(msg)
        messages.error(request, msg)
        return redirect('booking:group_detail', slug=slug)


def group_join_received(request, member_id, secure_token):
    """Confirmation page after a group join request is submitted."""
    member = get_object_or_404(
        GroupMember, member_id=member_id, secure_token=secure_token
    )
    return render(request, 'booking/group_join_received.html', {
        'member': member,
        'group':  member.group,
        'tour':   member.group.tour,
        'meta_title': f"Request Received — {member.member_id} | Structured Adventures",
    })


def group_join_status(request, member_id, secure_token):
    """Status page the client can check."""
    member = get_object_or_404(
        GroupMember, member_id=member_id, secure_token=secure_token
    )
    return render(request, 'booking/group_join_status.html', {
        'member': member,
        'group':  member.group,
        'tour':   member.group.tour,
    })


# ==============================================================================
# CONTACT FORM
# ==============================================================================

def contact(request):
    _save_last_url(request)
    if request.method == 'POST':
        form = ContactEnquiryForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    enquiry = form.save()
                    transaction.on_commit(
                        lambda e=enquiry: EmailService.send_contact_notification(e)
                    )
                if request.headers.get('HX-Request'):
                    return HttpResponse(
                        '<div class="rounded-2xl bg-green-50 border border-green-200 p-6 text-center">'
                        '<p class="font-bold text-green-800 text-lg">Message sent!</p>'
                        '<p class="text-green-700 mt-2 text-sm">We\'ll be in touch within 24 hours. '
                        'For urgent enquiries, WhatsApp us directly.</p>'
                        '</div>'
                    )
                messages.success(request, "Message sent! We'll be in touch within 24 hours.")
                return redirect('core:contact')
            except Exception:
                logger.exception("Contact form save failed")
                messages.error(request, "Something went wrong. Please try again.")
        if request.headers.get('HX-Request'):
            return _htmx_form_errors(form)
    else:
        form = ContactEnquiryForm()

    return render(request, 'core/contact.html', {
        'form': form,
        'meta_title': 'Contact Us | Structured Adventures',
    })


# ==============================================================================
# HTMX helpers
# ==============================================================================

def _htmx_form_errors(form):
    """Return inline HTML error list for HTMX form validation."""
    error_html = (
        '<div class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm">'
        '<p class="font-bold text-red-800 mb-2">Please fix the following:</p>'
        '<ul class="list-disc list-inside text-red-700 space-y-1">'
    )
    for field, errors in form.errors.items():
        label = form.fields[field].label if field in form.fields else field.replace('_', ' ').title()
        for error in errors:
            error_html += f'<li><strong>{label}:</strong> {error}</li>'
    for error in form.non_field_errors():
        error_html += f'<li>{error}</li>'
    error_html += '</ul></div>'
    return HttpResponse(error_html)


def _htmx_error(message):
    """Return a single error message HTML for HTMX."""
    return HttpResponse(
        f'<div class="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 text-sm font-semibold">'
        f'{message}</div>'
    )


# ==============================================================================
# Email dispatch helpers (called via on_commit)
# ==============================================================================

def _send_booking_emails(booking):
    """Fire both client and staff booking emails. Errors are logged, never raised."""
    try:
        EmailService.send_booking_received(booking)
    except Exception:
        logger.exception("Failed to send booking emails for %s", booking.booking_ref)


def _send_group_join_emails(member):
    """Fire both client and staff group join emails."""
    try:
        EmailService.send_group_join_received(member)
    except Exception:
        logger.exception("Failed to send group join emails for %s", member.member_id)
