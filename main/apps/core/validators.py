import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# Configurable via settings.py with sensible defaults
MAX_IMAGE_SIZE_MB = getattr(settings, 'MAX_IMAGE_SIZE_MB', 5)
ALLOWED_IMAGE_EXTENSIONS = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.webp'])

def validate_image_size(value, max_size_mb=None, field_name="image"):
    if not value:
        return

    # Unchanged CloudinaryField value on an existing record is a CloudinaryResource,
    # not an uploaded file — it has no .size and was already validated at upload time.
    if not hasattr(value, 'size'):
        return

    # --- File Size Validation ---
    max_size_mb = max_size_mb or MAX_IMAGE_SIZE_MB
    max_size_bytes = max_size_mb * 1024 * 1024

    if value.size > max_size_bytes:
        raise ValidationError(
            _('%(field)s too large (%(current_size)s MB). Maximum: %(max)s MB. '
              'Compress at tinypng.com or squoosh.app.'),
            params={
                'field': field_name,
                'current_size': round(value.size / (1024 * 1024), 2),
                'max': max_size_mb
            },
            code='image_too_large'
        )

    return value


def validate_image_format(value, allowed_extensions=None, allowed_mime_types=None, field_name="image"):
    if not value:
        return

    # Unchanged CloudinaryField value on an existing record is a CloudinaryResource,
    # not an uploaded file — it has no .name and was already validated at upload time.
    if not hasattr(value, 'name'):
        return

    exts = allowed_extensions or ALLOWED_IMAGE_EXTENSIONS
    mime_types = allowed_mime_types or ['image/jpeg', 'image/png', 'image/webp']

    # Extension check
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in [e.lower() for e in exts]:
        raise ValidationError(
            _('%(field)s format "%(ext)s" not allowed. Use: %(allowed)s.'),
            params={
                'field': field_name,
                'ext': ext,
                'allowed': ', '.join(exts),
            },
            code='invalid_extension'
        )

    # Content type check
    if hasattr(value, 'content_type') and value.content_type:
        if value.content_type not in mime_types:
            if not (value.content_type == 'image/jpg' and '.jpg' in exts):
                raise ValidationError(
                    _('%(field)s content type "%(mime)s" not valid.'),
                    params={'field': field_name, 'mime': value.content_type},
                    code='invalid_mime'
                )

    return value


def get_image_upload_help_text(max_size_mb=None, allowed_formats=None, field_type="hero"):
    max_size = max_size_mb or MAX_IMAGE_SIZE_MB
    formats = allowed_formats or ALLOWED_IMAGE_EXTENSIONS
    format_str = ', '.join(f.upper().replace('.', '') for f in formats)

    templates = {
        'hero': _(
            'Upload a high-quality hero image. '
            '• Max file size: %(max_size)s MB\n'
            '• Formats: %(formats)s\n'
            '• Tip: Use WebP for 30-50%% smaller files.'
        ),
        'gallery': _(
            'Gallery image for the photo slider. '
            '• Max file size: %(max_size)s MB\n'
            '• Formats: %(formats)s\n'
            '• Tip: Landscape (16:9) works best.'
        ),
        'og_image': _(
            'Social media preview image (Open Graph). '
            '• Max file size: %(max_size)s MB\n'
            '• Recommended: 1200 x 630 px (1.91:1 ratio)\n'
            '• Formats: %(formats)s\n'
            '• This appears when sharing on WhatsApp/Facebook.'
        ),
    }

    template = templates.get(field_type, templates['hero'])
    return template % {
        'max_size': max_size,
        'formats': format_str,
    }
