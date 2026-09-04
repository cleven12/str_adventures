from django.contrib import admin
from unfold.admin import ModelAdmin

from .admin_mixins import JSONImportMixin
from .admin_unfold import MARKDOWN_OVERRIDES
from .models import FAQ, JobPosting, SiteSettings, TeamMember, ContactMessage, JobApplication


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """
    ⚙️ Singleton-like Admin for global site settings.
    Ensures only one instance can be created.
    """
    list_display = ('site_name', 'contact_email', 'contact_phone', 'holiday_mode', 'holiday_name')
    fieldsets = (
        ('🏷️ Brand & Contact', {
            'fields': ('site_name', 'contact_email', 'contact_phone', 'whatsapp_number', 'office_address')
        }),
        ('📢 Announcements & Holidays', {
            'fields': (
                'show_announcement', 'announcement_text', 'announcement_link',
                'holiday_mode', 'holiday_name'
            ),
            'description': "Enable 'Holiday Mode' to trigger festive UI themes (Glassmorphism + Accent colors)."
        }),
        ('🔍 SEO Defaults', {
            'fields': ('default_meta_title', 'default_meta_description'),
            'description': "Fallback SEO tags when specific page data is missing."
        }),
    )

    def has_add_permission(self, request):
        # Prevent multiple SiteSettings instances
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the only SiteSettings instance
        return False


@admin.register(FAQ)
class FAQAdmin(JSONImportMixin, ModelAdmin):
    """❓ Admin for Managing Customer FAQs."""
    formfield_overrides = MARKDOWN_OVERRIDES
    json_import_key = 'question'
    list_display = ('question', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    ordering = ('order',)


@admin.register(TeamMember)
class TeamMemberAdmin(JSONImportMixin, ModelAdmin):
    """🧑‍🤝‍🧑 Admin for the guide/staff team roster."""
    json_import_key = 'name'
    list_display = ('name', 'role', 'years_experience', 'summits_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'role')
    search_fields = ('name', 'role', 'bio')
    ordering = ('order', 'name')


@admin.register(JobPosting)
class JobPostingAdmin(JSONImportMixin, ModelAdmin):
    """💼 Admin for open job postings."""
    json_import_key = 'slug'
    list_display = ('title', 'department', 'type', 'location', 'deadline', 'is_active')
    list_filter = ('type', 'department', 'is_active')
    search_fields = ('title', 'department', 'description', 'requirements')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    """📬 Admin for contact form submissions."""
    list_display = ('name', 'email', 'subject', 'email_sent', 'is_read', 'created_at')
    list_filter = ('email_sent', 'is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = (
        'name', 'email', 'phone', 'subject', 'message',
        'date_from', 'date_to', 'group_size', 'email_sent', 'created_at',
    )
    list_editable = ('is_read',)
    ordering = ('-created_at',)


@admin.register(JobApplication)
class JobApplicationAdmin(ModelAdmin):
    """📮 Admin for job applications submitted via the careers page."""
    list_display = ('name', 'email', 'job', 'cv', 'email_sent', 'is_read', 'created_at')
    list_filter = ('job', 'email_sent', 'is_read', 'created_at')
    search_fields = ('name', 'email', 'cover_letter', 'job__title')
    readonly_fields = (
        'job', 'name', 'email', 'cv', 'cover_letter', 'email_sent', 'created_at',
    )
    list_editable = ('is_read',)
    ordering = ('-created_at',)
