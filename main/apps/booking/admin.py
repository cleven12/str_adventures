# apps/booking/admin.py
# Structured Adventures — booking admin
#
# Staff workflow:
#   1. New booking lands in 'pending' → admin shows it prominently
#   2. Staff review, click 'Confirm Booking' action → status = confirmed
#   3. Staff generate DPO link in DPO dashboard, paste it into dpo_payment_url
#   4. Staff click 'Send DPO Link to Client' action → email fires
#   5. Client pays via DPO → staff click 'Mark Payment Confirmed' action
#
# Every action is a Django admin action so it's audited in the action log.

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from .models import Booking, GroupDeparture, GroupMember, ContactEnquiry, PaymentRecord
from apps.core.services.email_service import EmailService


# ==============================================================================
# BOOKING
# ==============================================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_ref', 'full_name', 'tour_link', 'travel_date',
        'num_people', 'status_badge', 'payment_badge',
        'dpo_url_set', 'created_at',
    ]
    list_filter  = ['status', 'payment_confirmed', 'preferred_contact', 'created_at']
    search_fields = ['booking_ref', 'full_name', 'email', 'phone_number']
    date_hierarchy = 'travel_date'
    ordering = ['-created_at']
    readonly_fields = [
        'booking_ref', 'secure_token', 'created_at', 'updated_at',
        'payment_confirmed_at', 'payment_confirmed_by',
        'client_status_url',
    ]

    fieldsets = [
        ('Reference', {
            'fields': ('booking_ref', 'secure_token', 'client_status_url'),
        }),
        ('Client Details', {
            'fields': (
                'full_name', 'email', 'phone_number', 'whatsapp_number',
                'country', 'preferred_contact',
            ),
        }),
        ('Trip Details', {
            'fields': (
                'tour', 'num_people', 'travel_date', 'flexible_dates',
                'experience_level', 'message',
            ),
        }),
        ('Status', {
            'fields': ('status', 'assigned_to'),
        }),
        ('Payment (Staff)', {
            'fields': (
                'quoted_price_usd',
                'dpo_payment_url', 'dpo_payment_url_sent',
                'payment_confirmed', 'payment_confirmed_at', 'payment_confirmed_by',
            ),
            'description': (
                '1. Agree price with client → fill Quoted Price. '
                '2. Generate DPO link in DPO dashboard → paste URL. '
                '3. Use "Send DPO Link" action to email client. '
                '4. Once client pays → use "Mark Payment Confirmed" action.'
            ),
        }),
        ('Staff Notes', {
            'fields': ('staff_notes',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    ]

    actions = [
        'action_confirm_bookings',
        'action_send_dpo_link',
        'action_mark_payment_confirmed',
    ]

    # ── Display helpers ────────────────────────────────────────────────────────

    def tour_link(self, obj):
        return format_html(
            '<a href="/admin/tours/tour/{}/change/">{}</a>',
            obj.tour_id, obj.tour.title
        )
    tour_link.short_description = 'Tour'

    def status_badge(self, obj):
        colours = {
            'pending':   '#f59e0b',
            'confirmed': '#10b981',
            'cancelled': '#ef4444',
            'completed': '#6366f1',
        }
        colour = colours.get(obj.status, '#94a3b8')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:999px;font-size:11px;font-weight:700">{}</span>',
            colour, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_badge(self, obj):
        if obj.payment_confirmed:
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:2px 8px;'
                'border-radius:999px;font-size:11px;font-weight:700">✓ Paid</span>'
            )
        return format_html(
            '<span style="background:#e2e8f0;color:#64748b;padding:2px 8px;'
            'border-radius:999px;font-size:11px">Unpaid</span>'
        )
    payment_badge.short_description = 'Payment'

    def dpo_url_set(self, obj):
        if obj.dpo_payment_url:
            sent = ' ✓ sent' if obj.dpo_payment_url_sent else ' (not sent)'
            return format_html(
                '<span style="color:#10b981;font-weight:700">Link ready{}</span>', sent
            )
        return format_html('<span style="color:#94a3b8">No link yet</span>')
    dpo_url_set.short_description = 'DPO Link'

    def client_status_url(self, obj):
        url = obj.get_confirm_url()
        full = f"https://{__import__('django.conf', fromlist=['settings']).settings.SITE_DOMAIN}{url}"
        return format_html('<a href="{}" target="_blank">{}</a>', full, full)
    client_status_url.short_description = 'Client Status Page'

    # ── Actions ────────────────────────────────────────────────────────────────

    def action_confirm_bookings(self, request, queryset):
        confirmed = 0
        for booking in queryset.filter(status='pending'):
            booking.confirm(staff_user=request.user)
            confirmed += 1
        self.message_user(
            request,
            f"{confirmed} booking(s) confirmed. Clients have been notified.",
            messages.SUCCESS,
        )
    action_confirm_bookings.short_description = "✓ Confirm selected bookings"

    def action_send_dpo_link(self, request, queryset):
        sent, skipped = 0, 0
        for booking in queryset:
            if not booking.dpo_payment_url:
                skipped += 1
                continue
            if EmailService.send_dpo_link_notification(booking):
                booking.dpo_payment_url_sent = True
                booking.save(update_fields=['dpo_payment_url_sent', 'updated_at'])
                sent += 1
            else:
                skipped += 1
        if sent:
            self.message_user(request, f"DPO link sent to {sent} client(s).", messages.SUCCESS)
        if skipped:
            self.message_user(
                request,
                f"{skipped} booking(s) skipped — no DPO URL set or email failed.",
                messages.WARNING,
            )
    action_send_dpo_link.short_description = "→ Send DPO payment link to client"

    def action_mark_payment_confirmed(self, request, queryset):
        confirmed = 0
        for booking in queryset.filter(payment_confirmed=False):
            booking.mark_payment_confirmed(confirmed_by=request.user)
            confirmed += 1
        self.message_user(
            request,
            f"{confirmed} payment(s) marked as confirmed.",
            messages.SUCCESS,
        )
    action_mark_payment_confirmed.short_description = "$ Mark payment confirmed"


# ==============================================================================
# GROUP DEPARTURE
# ==============================================================================

class GroupMemberInline(admin.TabularInline):
    model  = GroupMember
    extra  = 0
    readonly_fields = [
        'member_id', 'full_name', 'email', 'phone_number',
        'country', 'party_size', 'status', 'payment_confirmed', 'joined_at',
    ]
    fields = readonly_fields
    can_delete = False
    show_change_link = True


@admin.register(GroupDeparture)
class GroupDepartureAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'tour_name', 'start_date', 'fill_display',
        'status', 'is_active', 'show_on_homepage',
    ]
    list_filter  = ['status', 'is_active', 'show_on_homepage', 'start_date']
    search_fields = ['title', 'tour__title']
    date_hierarchy = 'start_date'
    prepopulated_fields = {'slug': ('title',)}
    inlines = [GroupMemberInline]
    readonly_fields = ['current_count', 'created_at', 'updated_at']

    fieldsets = [
        ('Trip Details', {
            'fields': (
                'tour', 'title', 'slug', 'description',
                'start_date', 'end_date', 'expires_at',
            ),
        }),
        ('Capacity & Pricing', {
            'fields': (
                'capacity', 'min_participants', 'current_count',
                'price_per_person',
            ),
        }),
        ('Display', {
            'fields': (
                'status', 'is_active', 'show_on_homepage',
                'feature_badge', 'benefits_text',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    ]

    def tour_name(self, obj):
        return obj.tour.title
    tour_name.short_description = 'Tour'

    def fill_display(self, obj):
        pct = obj.fill_percentage
        colour = '#10b981' if pct >= 80 else '#f59e0b' if pct >= 50 else '#94a3b8'
        return format_html(
            '<span style="color:{};font-weight:700">{}/{} ({}%)</span>',
            colour, obj.current_count, obj.capacity, pct
        )
    fill_display.short_description = 'Filled'


# ==============================================================================
# GROUP MEMBER
# ==============================================================================

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = [
        'member_id', 'full_name', 'group_title',
        'party_size', 'status_badge', 'payment_badge',
        'dpo_url_set', 'joined_at',
    ]
    list_filter  = ['status', 'payment_confirmed', 'joined_at']
    search_fields = ['member_id', 'full_name', 'email', 'phone_number']
    ordering = ['-joined_at']
    readonly_fields = [
        'member_id', 'secure_token', 'joined_at', 'updated_at',
        'payment_confirmed_at', 'payment_confirmed_by',
        'total_price_display',
    ]

    fieldsets = [
        ('Reference', {
            'fields': ('member_id', 'secure_token', 'group'),
        }),
        ('Client Details', {
            'fields': (
                'full_name', 'email', 'phone_number', 'whatsapp_number',
                'country', 'party_size', 'message',
            ),
        }),
        ('Trip Price', {
            'fields': ('total_price_display',),
        }),
        ('Status', {
            'fields': ('status', 'staff_notes'),
        }),
        ('Payment (Staff)', {
            'fields': (
                'dpo_payment_url',
                'payment_confirmed', 'payment_confirmed_at', 'payment_confirmed_by',
            ),
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    ]

    actions = [
        'action_accept',
        'action_reject',
        'action_send_dpo_link',
        'action_mark_payment_confirmed',
    ]

    def group_title(self, obj):
        return obj.group.title
    group_title.short_description = 'Group'

    def status_badge(self, obj):
        colours = {
            'pending':   '#f59e0b',
            'accepted':  '#10b981',
            'rejected':  '#ef4444',
            'cancelled': '#94a3b8',
        }
        colour = colours.get(obj.status, '#94a3b8')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:999px;font-size:11px;font-weight:700">{}</span>',
            colour, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_badge(self, obj):
        if obj.payment_confirmed:
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:2px 8px;'
                'border-radius:999px;font-size:11px;font-weight:700">✓ Paid</span>'
            )
        return format_html('<span style="color:#94a3b8;font-size:11px">Unpaid</span>')
    payment_badge.short_description = 'Payment'

    def dpo_url_set(self, obj):
        if obj.dpo_payment_url:
            return format_html('<span style="color:#10b981;font-weight:700">✓ Link set</span>')
        return format_html('<span style="color:#94a3b8">—</span>')
    dpo_url_set.short_description = 'DPO Link'

    def total_price_display(self, obj):
        return f"${obj.total_price:,.2f} USD ({obj.party_size} × ${obj.price_per_person:,.2f})"
    total_price_display.short_description = 'Total Price'

    # ── Actions ────────────────────────────────────────────────────────────────

    def action_accept(self, request, queryset):
        accepted = 0
        for member in queryset.filter(status='pending'):
            member.accept(staff_user=request.user)
            accepted += 1
        self.message_user(request, f"{accepted} member(s) accepted.", messages.SUCCESS)
    action_accept.short_description = "✓ Accept selected join requests"

    def action_reject(self, request, queryset):
        rejected = 0
        for member in queryset.filter(status='pending'):
            member.reject()
            rejected += 1
        self.message_user(request, f"{rejected} member(s) rejected.", messages.SUCCESS)
    action_reject.short_description = "✗ Reject selected join requests"

    def action_send_dpo_link(self, request, queryset):
        sent, skipped = 0, 0
        for member in queryset:
            if not member.dpo_payment_url:
                skipped += 1
                continue
            if EmailService.send_group_dpo_link_notification(member):
                sent += 1
            else:
                skipped += 1
        if sent:
            self.message_user(request, f"DPO link sent to {sent} member(s).", messages.SUCCESS)
        if skipped:
            self.message_user(
                request,
                f"{skipped} member(s) skipped — no URL set or email failed.",
                messages.WARNING,
            )
    action_send_dpo_link.short_description = "→ Send DPO payment link to client"

    def action_mark_payment_confirmed(self, request, queryset):
        confirmed = 0
        for member in queryset.filter(payment_confirmed=False):
            member.mark_payment_confirmed(confirmed_by=request.user)
            confirmed += 1
        self.message_user(
            request, f"{confirmed} payment(s) confirmed.", messages.SUCCESS
        )
    action_mark_payment_confirmed.short_description = "$ Mark payment confirmed"


# ==============================================================================
# CONTACT ENQUIRY
# ==============================================================================

@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'topic', 'subject', 'is_read', 'created_at']
    list_filter   = ['topic', 'is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering      = ['-created_at']
    readonly_fields = ['created_at']
    actions       = ['mark_read']

    def mark_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, "Marked as read.", messages.SUCCESS)
    mark_read.short_description = "Mark selected as read"


# ==============================================================================
# PAYMENT RECORD
# ==============================================================================

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display  = [
        'booking_or_member', 'amount_usd', 'dpo_reference',
        'payment_method', 'recorded_by', 'recorded_at',
    ]
    list_filter   = ['payment_method', 'recorded_at']
    search_fields = ['dpo_reference', 'booking__booking_ref', 'group_member__member_id']
    readonly_fields = ['recorded_at']

    def booking_or_member(self, obj):
        if obj.booking:
            return f"Booking: {obj.booking.booking_ref}"
        if obj.group_member:
            return f"Member: {obj.group_member.member_id}"
        return "—"
    booking_or_member.short_description = 'For'
