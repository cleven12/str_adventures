# config/settings_diff.py
#
# STRUCTURED ADVENTURES — settings changes from the visitkili base
# Apply these changes on top of your existing config/settings.py
# ──────────────────────────────────────────────────────────────────
#
# 1. REMOVE from INSTALLED_APPS:
#    'apps.ai_chat',       # not needed yet
#    'apps.indexing',      # remove if not using Google Indexing API
#
# 2. ADD / CHANGE these settings:

# ── Site identity ──────────────────────────────────────────────────
SITE_NAME   = config('SITE_NAME', default='Structured Adventures')
SITE_DOMAIN = config('SITE_DOMAIN', default='structuredadventures.com')

# WhatsApp number in international format e.g. +255741788255
WHATSAPP_NUMBER = config('WHATSAPP_NUMBER', default='+255741788255')

# ── Staff notifications ─────────────────────────────────────────────
# Comma-separated list of staff email addresses that receive booking alerts
# e.g. STAFF_EMAILS=ops@structuredadventures.com,reservations@structuredadventures.com
STAFF_EMAILS = config('STAFF_EMAILS', default='', cast=Csv())

CONTACT_EMAIL    = config('CONTACT_EMAIL', default='info@structuredadventures.com')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='Structured Adventures <noreply@structuredadventures.com>'
)

# ── Email backend ──────────────────────────────────────────────────
# Production: use your SMTP credentials (Zoho, Gmail SMTP, Mailgun, etc.)
EMAIL_BACKEND  = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST     = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT     = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS  = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER     = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# ── DPO settings ───────────────────────────────────────────────────
# DPO is used OFFLINE — staff generate links in the DPO dashboard.
# These settings are stored here so the DPO base URL is available
# for staff to know where to go, but NO API calls are made from Django.
#
# Staff workflow:
#   1. Log in to https://merchant.dpo.group/
#   2. Create a custom payment link for the agreed amount
#   3. Copy the URL
#   4. Paste into Booking.dpo_payment_url in the Django admin
#   5. Use the admin action "Send DPO Link to Client"
#
DPO_MERCHANT_DASHBOARD = 'https://merchant.dpo.group/'
DPO_COMPANY_TOKEN      = config('DPO_COMPANY_TOKEN', default='')  # kept for reference

# ── REMOVE these from .env (no longer used) ────────────────────────
# DPO_SERVICE_TYPE
# DPO_API_URL
# DPO_PAYMENT_URL
# DPO_REDIRECT_BASE_URL
# Pinecone / AI chat keys (if removing ai_chat app)

# ── Logging ─────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps.booking': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.core.services.email_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
