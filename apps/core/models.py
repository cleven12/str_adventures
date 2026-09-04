from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse
from cloudinary.models import CloudinaryField
from cloudinary_storage.storage import RawMediaCloudinaryStorage

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="VISIT KILI ADVNTURES")
    contact_email = models.EmailField(default="info@visitkili.com")
    contact_phone = models.CharField(max_length=20, default="+255...")
    whatsapp_number = models.CharField(max_length=20, blank=True)
    office_address = models.TextField(blank=True)
    
    # Global Announcement / Holiday Widget
    show_announcement = models.BooleanField(default=False)
    announcement_text = models.CharField(max_length=255, blank=True)
    announcement_link = models.URLField(blank=True)
    holiday_mode = models.BooleanField(default=False, help_text="Enable for special UI themes (e.g. Eid, Christmas)")
    holiday_name = models.CharField(max_length=50, blank=True, help_text="e.g. Eid Mubarak")

    # SEO Defaults
    default_meta_title = models.CharField(max_length=60, blank=True)
    default_meta_description = models.CharField(max_length=155, blank=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def get_organization_schema(self):
        """
        Generate JSON-LD for LocalBusiness / Organization.
        """
        from django.conf import settings
        domain = getattr(settings, 'SITE_DOMAIN', 'visitkili.com')
        return {
            "@context": "https://schema.org",
            "@type": "TravelAgency",
            "name": self.site_name,
            "url": f"https://{domain}",
            "logo": "https://res.cloudinary.com/ducpxtvfj/image/upload/v1771429157/apple-icon-180x180_dc6jsh.png",
            "email": self.contact_email,
            "telephone": self.contact_phone,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": self.office_address,
                "addressLocality": "Moshi",
                "addressRegion": "Kilimanjaro",
                "addressCountry": "TZ"
            },
            "sameAs": [
                f"https://wa.me/{self.whatsapp_number.replace('+', '').replace(' ', '')}" if self.whatsapp_number else "",
                "https://www.instagram.com/visitkili",
                "https://www.facebook.com/visitkili"
            ]
        }

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = CKEditor5Field(config_name='default')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question

    @staticmethod
    def get_faq_page_schema(faqs):
        """
        Generate FAQPage JSON-LD for a list of FAQs.
        Cleans HTML for cleaner search result snippets.
        """
        from django.utils.html import strip_tags
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq.question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": strip_tags(faq.answer)
                    }
                } for faq in faqs
            ]
        }


class TeamMember(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    photo = CloudinaryField('image', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    linkedin = models.URLField(blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    summits_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.role}"


class JobPosting(models.Model):
    FULL_TIME = 'full_time'
    INTERNSHIP = 'internship'
    VOLUNTEER = 'volunteer'

    TYPE_CHOICES = [
        (FULL_TIME, 'Full time'),
        (INTERNSHIP, 'Internship'),
        (VOLUNTEER, 'Volunteer'),
    ]

    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    department = models.CharField(max_length=120)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=FULL_TIME)
    location = models.CharField(max_length=120, default='Moshi, Tanzania')
    description = models.TextField()
    requirements = models.TextField()
    is_active = models.BooleanField(default=True)
    deadline = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:career_detail', kwargs={'slug': self.slug})


class ContactMessage(models.Model):
    """Stores every contact form submission so staff can review it in admin,
    independent of whether the notification email actually sent."""
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    date_from = models.CharField(max_length=40, blank=True)
    date_to = models.CharField(max_length=40, blank=True)
    group_size = models.CharField(max_length=40, blank=True)
    email_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.subject or 'Contact Form Inquiry'}"


class JobApplication(models.Model):
    """Stores every job application submission so staff can review it in
    admin, independent of whether the notification email actually sent."""
    job = models.ForeignKey(
        JobPosting, on_delete=models.CASCADE, related_name='applications'
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    cv = models.FileField(
        upload_to='careers/cv/', blank=True, null=True,
        storage=RawMediaCloudinaryStorage(),
    )
    cover_letter = models.TextField(blank=True)
    email_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.job.title}"
