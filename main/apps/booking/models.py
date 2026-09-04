# apps/booking/models.py
# Structured Adventures — booking layer
#
# Design philosophy:
#   • NO payment processing on-site. Zero gateway calls from this codebase.
#   • Bookings are ENQUIRIES that get saved to DB + email staff.
#   • Payment happens offline via a custom DPO URL generated per-booking.
#   • Staff send the DPO link manually (WhatsApp / email) once they confirm
#     dates and agree on the price with the client.
#   • PaymentTransaction is kept purely as an audit log when staff manually
#     record that a DPO payment was completed. It is NOT triggered by the web.

import uuid
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField

User = get_user_model()


# ── ID generators ──────────────────────────────────────────────────────────────

def generate_booking_ref():
    """Human-friendly 8-char uppercase reference e.g. SA3F9B2C"""
    return f"SA{get_random_string(6).upper()}"


def generate_secure_token():
    """URL-safe 32-char hex token for unguessable confirm/cancel links."""
    return uuid.uuid4().hex


# ==============================================================================
# GROUP DEPARTURE — fixed-date shared trips
# ==============================================================================

class GroupDeparture(models.Model):
    STATUS_CHOICES = [
        ('open',      'Open for Bookings'),
        ('filling',   'Filling Fast'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    BADGE_CHOICES = [
        ('hot',         'Hot Deal'),
        ('last_chance', 'Last Chance'),
        ('almost_full', 'Almost Full'),
        ('confirmed',   'Confirmed'),
        ('new',         'New'),
    ]

    tour            = models.ForeignKey(
        'tours.Tour', on_delete=models.CASCADE, related_name='group_departures'
    )
    title           = models.CharField(max_length=200)
    slug            = models.SlugField(unique=True, blank=True)
    start_date      = models.DateTimeField()
    end_date        = models.DateTimeField()
    capacity        = models.PositiveIntegerField()
    min_participants = models.PositiveIntegerField(default=2)
    current_count   = models.PositiveIntegerField(default=0)

    # Displayed price — the actual price clients see. Staff decide any
    # adjustments before sending the DPO link.
    price_per_person = models.DecimalField(max_digits=8, decimal_places=2)

    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open'
    )
    expires_at      = models.DateTimeField(
        help_text="Deadline — no new join requests after this date"
    )
    feature_badge   = models.CharField(
        max_length=20, choices=BADGE_CHOICES, blank=True
    )
    show_on_homepage = models.BooleanField(default=False)
    benefits_text   = models.TextField(
        blank=True, help_text="e.g. 'Free airport transfer from Arusha'"
    )
    description     = models.TextField(blank=True)
    is_active       = models.BooleanField(default=True)
    created_by      = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_departures'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'group_departures'
        ordering            = ['start_date']
        verbose_name        = 'Group Departure'
        verbose_name_plural = 'Group Departures'
        indexes = [
            models.Index(fields=['tour', 'status', 'is_active'], name='gdep_tour_status_idx'),
            models.Index(fields=['start_date', 'status'],         name='gdep_date_status_idx'),
            models.Index(fields=['expires_at', 'status'],         name='gdep_expires_idx'),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_date.strftime('%b %Y')})"

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date.")
        if self.min_participants > self.capacity:
            raise ValidationError("Min participants cannot exceed capacity.")

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while GroupDeparture.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"/booking/groups/{self.slug}/"

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def spots_remaining(self):
        return max(0, self.capacity - self.current_count)

    @property
    def is_accepting_requests(self):
        """True if the group can still receive join requests."""
        return (
            self.is_active
            and self.status in ['open', 'filling']
            and self.spots_remaining > 0
            and self.expires_at > timezone.now()
        )

    @property
    def fill_percentage(self):
        if not self.capacity:
            return 0
        return int((self.current_count / self.capacity) * 100)

    @property
    def has_reached_minimum(self):
        return self.current_count >= self.min_participants

    @property
    def days_until_departure(self):
        delta = self.start_date - timezone.now()
        return max(0, delta.days)

    @property
    def urgency_label(self):
        if self.fill_percentage >= 90:
            return "Almost Full"
        if self.fill_percentage >= 70:
            return "Filling Fast"
        if self.has_reached_minimum:
            return "Trip Confirmed"
        return None

    def recalculate_count(self):
        """Recount accepted members (status='accepted') and save."""
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            locked = GroupDeparture.objects.select_for_update().get(pk=self.pk)
            total = (
                locked.members
                .filter(status='accepted')
                .aggregate(total=models.Sum('party_size'))['total'] or 0
            )
            new_status = locked.status
            if total >= locked.capacity:
                new_status = 'confirmed'
            elif total >= locked.min_participants and locked.status == 'open':
                new_status = 'filling'
            locked.current_count = total
            locked.status = new_status
            locked.save(update_fields=['current_count', 'status'])
            self.current_count = locked.current_count
            self.status = locked.status


# ==============================================================================
# GROUP MEMBER — someone who requests to join a GroupDeparture
# ==============================================================================

class GroupMember(models.Model):
    """
    A join *request*. Status flow:
        pending → accepted (staff confirm, send DPO link manually)
                → rejected (no space / declined)
                → cancelled (client withdrew)
    Payment is NOT tracked here — that's a manual DPO process off-site.
    """

    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('accepted',  'Accepted'),
        ('rejected',  'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    group           = models.ForeignKey(
        GroupDeparture, on_delete=models.CASCADE, related_name='members'
    )
    member_id       = models.CharField(
        max_length=12, unique=True, blank=True, editable=False,
        help_text="Auto-generated reference e.g. SAGM3F9B"
    )
    secure_token    = models.CharField(
        max_length=32, unique=True,
        default=generate_secure_token, editable=False, db_index=True
    )

    # ── Client info ────────────────────────────────────────────────────────────
    full_name       = models.CharField(max_length=100)
    email           = models.EmailField()
    phone_number    = models.CharField(max_length=25)
    whatsapp_number = models.CharField(
        max_length=25, blank=True,
        help_text="If different from phone — staff will use this for payment link"
    )
    country         = CountryField(blank_label='(Select Country)', default='TZ')
    party_size      = models.PositiveIntegerField(
        default=1, help_text="Number of people in this party"
    )
    message         = models.TextField(
        blank=True, help_text="Special requests, dietary needs, experience level, etc."
    )

    # ── Status ─────────────────────────────────────────────────────────────────
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )

    # ── Staff notes ────────────────────────────────────────────────────────────
    staff_notes     = models.TextField(
        blank=True,
        help_text="Internal notes — not visible to client"
    )
    # DPO payment link generated manually by staff and sent via WhatsApp/email
    dpo_payment_url = models.URLField(
        blank=True,
        help_text="Custom DPO payment URL — staff generate and send to client"
    )
    payment_confirmed = models.BooleanField(
        default=False,
        help_text="Staff manually tick once DPO payment is confirmed"
    )
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    payment_confirmed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='confirmed_group_payments'
    )

    joined_at       = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'group_members'
        ordering            = ['-joined_at']
        verbose_name        = 'Group Member'
        verbose_name_plural = 'Group Members'
        indexes = [
            models.Index(fields=['group', 'status'],        name='gmember_group_status_idx'),
            models.Index(fields=['email'],                  name='gmember_email_idx'),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.party_size} pax) — {self.group.title}"

    def save(self, *args, **kwargs):
        if not self.member_id:
            mid = f"SAGM{get_random_string(6).upper()}"
            while GroupMember.objects.filter(member_id=mid).exists():
                mid = f"SAGM{get_random_string(6).upper()}"
            self.member_id = mid
        super().save(*args, **kwargs)

    @property
    def price_per_person(self):
        return self.group.price_per_person

    @property
    def total_price(self):
        return self.group.price_per_person * self.party_size

    @property
    def preferred_contact(self):
        """Return the best contact number for staff to use."""
        return self.whatsapp_number or self.phone_number

    def accept(self, staff_user=None, notes=''):
        """Staff action: accept the join request and trigger notification email."""
        from django.db import transaction as db_transaction
        from apps.core.services.email_service import EmailService
        with db_transaction.atomic():
            self.status = 'accepted'
            if notes:
                self.staff_notes = notes
            self.save(update_fields=['status', 'staff_notes', 'updated_at'])
            self.group.recalculate_count()
        db_transaction.on_commit(lambda: EmailService.send_group_member_accepted(self))

    def reject(self, staff_user=None, notes=''):
        """Staff action: reject the join request."""
        self.status = 'rejected'
        if notes:
            self.staff_notes = notes
        self.save(update_fields=['status', 'staff_notes', 'updated_at'])

    def mark_payment_confirmed(self, confirmed_by=None):
        """Staff action: manually confirm payment after DPO payment is verified."""
        self.payment_confirmed = True
        self.payment_confirmed_at = timezone.now()
        if confirmed_by:
            self.payment_confirmed_by = confirmed_by
        self.save(update_fields=[
            'payment_confirmed', 'payment_confirmed_at',
            'payment_confirmed_by', 'updated_at'
        ])


# ==============================================================================
# BOOKING — individual tour booking request
# ==============================================================================

class Booking(models.Model):
    """
    An individual booking request from a client.
    This is an ENQUIRY, not a payment.

    Flow:
        Client submits form → saved to DB → email sent to staff + client
        Staff review → WhatsApp/email client → agree on date/price
        Staff generate DPO payment link → send to client
        Client pays via DPO → staff manually confirm here
    """

    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    CONTACT_METHOD_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email',    'Email'),
        ('phone',    'Phone Call'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('beginner',      'Beginner — first trek'),
        ('intermediate',  'Intermediate — some hiking experience'),
        ('experienced',   'Experienced — regular hiker'),
        ('advanced',      'Advanced — high altitude experience'),
    ]

    # ── Core references ────────────────────────────────────────────────────────
    tour            = models.ForeignKey(
        'tours.Tour', on_delete=models.CASCADE, related_name='bookings'
    )
    booking_ref     = models.CharField(
        max_length=12, unique=True,
        default=generate_booking_ref, editable=False,
        help_text="Human-readable reference e.g. SA3F9B2C"
    )
    secure_token    = models.CharField(
        max_length=32, unique=True,
        default=generate_secure_token, editable=False, db_index=True
    )

    # ── Client info ────────────────────────────────────────────────────────────
    full_name       = models.CharField(max_length=100)
    email           = models.EmailField()
    phone_number    = models.CharField(max_length=25)
    whatsapp_number = models.CharField(
        max_length=25, blank=True,
        help_text="If different from phone"
    )
    country         = CountryField(blank_label='(Select Country)', default='TZ')
    num_people      = models.PositiveIntegerField(default=1)
    travel_date     = models.DateField()
    flexible_dates  = models.BooleanField(
        default=False,
        help_text="Client is flexible on the exact travel date"
    )
    preferred_contact = models.CharField(
        max_length=20, choices=CONTACT_METHOD_CHOICES, default='whatsapp'
    )
    experience_level = models.CharField(
        max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, blank=True
    )
    message         = models.TextField(
        blank=True,
        help_text="Special requests, dietary needs, accommodation preferences, etc."
    )

    # ── Status ─────────────────────────────────────────────────────────────────
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )

    # ── Staff fields ───────────────────────────────────────────────────────────
    staff_notes     = models.TextField(
        blank=True,
        help_text="Internal notes — not visible to client"
    )
    quoted_price_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Agreed price in USD — fill before generating DPO link"
    )
    # Staff generate this manually via DPO dashboard and paste it here
    dpo_payment_url = models.URLField(
        blank=True,
        help_text="Custom DPO payment URL to send to client"
    )
    dpo_payment_url_sent = models.BooleanField(
        default=False,
        help_text="Has the DPO link been sent to the client?"
    )
    payment_confirmed = models.BooleanField(
        default=False,
        help_text="Tick once DPO payment is confirmed by staff"
    )
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    payment_confirmed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='confirmed_bookings'
    )
    assigned_to     = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_bookings',
        help_text="Staff member handling this booking"
    )

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'bookings'
        ordering            = ['-created_at']
        verbose_name_plural = 'Bookings'
        indexes = [
            models.Index(fields=['booking_ref'],       name='booking_ref_idx'),
            models.Index(fields=['tour', 'status'],    name='booking_tour_status_idx'),
            models.Index(fields=['travel_date'],       name='booking_travel_date_idx'),
            models.Index(fields=['status', 'payment_confirmed'], name='booking_status_pay_idx'),
            models.Index(fields=['email'],             name='booking_email_idx'),
        ]

    def __str__(self):
        return f"{self.full_name} — {self.tour.title} [{self.booking_ref}]"

    def clean(self):
        if self.travel_date and self.travel_date < timezone.now().date():
            raise ValidationError("Travel date cannot be in the past.")
        if not self.email and not self.phone_number:
            raise ValidationError("Provide at least an email or phone number.")

    @property
    def preferred_contact_value(self):
        if self.preferred_contact == 'whatsapp':
            return self.whatsapp_number or self.phone_number
        if self.preferred_contact == 'phone':
            return self.phone_number
        return self.email

    @property
    def display_price(self):
        """Best price to show staff — quoted price if set, else tour list price."""
        if self.quoted_price_usd:
            return self.quoted_price_usd
        return getattr(self.tour, 'price_usd', None)

    def confirm(self, staff_user=None, notes=''):
        """Staff action: confirm the booking request."""
        from apps.core.services.email_service import EmailService
        self.status = 'confirmed'
        if notes:
            self.staff_notes = notes
        if staff_user:
            self.assigned_to = staff_user
        self.save(update_fields=['status', 'staff_notes', 'assigned_to', 'updated_at'])
        EmailService.send_booking_confirmed(self)

    def mark_payment_confirmed(self, confirmed_by=None):
        """Staff action: mark DPO payment as received."""
        self.payment_confirmed = True
        self.payment_confirmed_at = timezone.now()
        if confirmed_by:
            self.payment_confirmed_by = confirmed_by
        self.status = 'confirmed'
        self.save(update_fields=[
            'payment_confirmed', 'payment_confirmed_at',
            'payment_confirmed_by', 'status', 'updated_at'
        ])

    def get_confirm_url(self):
        return f"/booking/status/{self.booking_ref}/{self.secure_token}/"


# ==============================================================================
# CONTACT ENQUIRY — general website contact form submissions
# ==============================================================================

class ContactEnquiry(models.Model):
    """
    Simple contact form submission. Saved to DB so staff can review
    in the admin even if email delivery fails.
    """
    TOPIC_CHOICES = [
        ('kilimanjaro', 'Kilimanjaro Climbing'),
        ('safari',      'Safari'),
        ('zanzibar',    'Zanzibar Beach'),
        ('day_trip',    'Day Trip'),
        ('group',       'Group Tour'),
        ('custom',      'Custom Itinerary'),
        ('other',       'Other'),
    ]

    name            = models.CharField(max_length=100)
    email           = models.EmailField()
    phone           = models.CharField(max_length=25, blank=True)
    topic           = models.CharField(
        max_length=20, choices=TOPIC_CHOICES, default='other'
    )
    subject         = models.CharField(max_length=200)
    message         = models.TextField()
    is_read         = models.BooleanField(default=False)
    staff_notes     = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'contact_enquiries'
        ordering            = ['-created_at']
        verbose_name        = 'Contact Enquiry'
        verbose_name_plural = 'Contact Enquiries'

    def __str__(self):
        return f"{self.name} — {self.subject} ({self.created_at.strftime('%d %b %Y')})"


# ==============================================================================
# PAYMENT AUDIT LOG — manual record of DPO payments confirmed by staff
# ==============================================================================

class PaymentRecord(models.Model):
    """
    Staff manually create one of these when a DPO payment is confirmed.
    This is purely an audit trail — no gateway calls are made from this model.
    """
    booking         = models.ForeignKey(
        Booking, on_delete=models.CASCADE,
        related_name='payment_records', null=True, blank=True
    )
    group_member    = models.ForeignKey(
        GroupMember, on_delete=models.CASCADE,
        related_name='payment_records', null=True, blank=True
    )
    amount_usd      = models.DecimalField(max_digits=10, decimal_places=2)
    dpo_reference   = models.CharField(
        max_length=100, blank=True,
        help_text="DPO transaction reference from the DPO dashboard"
    )
    payment_method  = models.CharField(
        max_length=50, blank=True,
        help_text="e.g. Visa, M-Pesa, bank transfer"
    )
    notes           = models.TextField(blank=True)
    recorded_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    recorded_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_records'
        ordering = ['-recorded_at']

    def __str__(self):
        ref = self.booking or self.group_member
        return f"Payment ${self.amount_usd} — {ref} [{self.dpo_reference}]"
