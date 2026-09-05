# config/settings.py — Structured Adventures
from pathlib import Path
import importlib.util
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

STATICFILES_STORAGE_BACKEND = (
    "whitenoise.storage.CompressedStaticFilesStorage"
    if importlib.util.find_spec("whitenoise")
    else "django.contrib.staticfiles.storage.StaticFilesStorage"
)

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=1, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in config('CSRF_TRUSTED_ORIGINS',
        default='http://localhost:8000,https://structuredadventures.com', cast=Csv())
    if o and o.strip()
]
CSRF_FAILURE_VIEW = 'apps.core.views.custom_csrf_failure'

SECURE_SSL_REDIRECT             = config('SECURE_SSL_REDIRECT',             default=False, cast=bool)
SESSION_COOKIE_SECURE           = config('SESSION_COOKIE_SECURE',           default=False, cast=bool)
CSRF_COOKIE_SECURE              = config('CSRF_COOKIE_SECURE',              default=False, cast=bool)
SECURE_BROWSER_XSS_FILTER      = config('SECURE_BROWSER_XSS_FILTER',      default=True,  cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF    = config('SECURE_CONTENT_TYPE_NOSNIFF',    default=True,  cast=bool)
SECURE_HSTS_SECONDS            = config('SECURE_HSTS_SECONDS',            default=0,     cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD            = config('SECURE_HSTS_PRELOAD',            default=False, cast=bool)
X_FRAME_OPTIONS                = config('X_FRAME_OPTIONS',                default='DENY')
SECURE_REFERRER_POLICY         = config('SECURE_REFERRER_POLICY',         default='same-origin')
if config('USE_PROXY_SSL_HEADER', default=True, cast=bool):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Apps ────────────────────────────────────────────────────────────────────────
CUSTOM_APPS = [
    'apps.booking',
    'apps.core',
    'apps.destinations',
    'apps.guide',
    'apps.itinerary',
    'apps.reviews',
    'apps.tours',
]
THIRD_PARTY_APPS = [
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
    'django_ckeditor_5',
    'django_countries',
    'cloudinary',
    'cloudinary_storage',
]
UNFOLD_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
]
BUILT_IN_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
]
INSTALLED_APPS = UNFOLD_APPS + CUSTOM_APPS + BUILT_IN_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'apps.core.middleware.LegacyRedirectMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'apps.core.middleware.RateLimitMiddleware',
    'apps.core.middleware.SessionRedirectMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_settings',
                'apps.core.context_processors.tour_navigation',
                'apps.core.context_processors.brand_rating',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ] if not DEBUG else [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Frontend (Next.js) ────────────────────────────────────────────────────────────
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# ── CORS ────────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in config(
        'CORS_ALLOWED_ORIGINS',
        default='http://localhost:3000,https://structuredadventures.com,https://www.structuredadventures.com',
        cast=Csv(),
    )
    if o and o.strip()
]
CORS_ALLOW_CREDENTIALS = False  # API is public read — no cookies needed

# ── Django REST Framework ─────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # Public read-only — no auth on GET endpoints
    "DEFAULT_PERMISSION_CLASSES":    ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],

    # Filtering + search + ordering on all viewsets
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],

    # Auto OpenAPI schema generation
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    # Standard pagination — overridden per viewset where needed
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,

    # Return JSON everywhere
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],

    # Throttle public endpoints (adjust for production)
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "300/hour",   # 300 requests/hour per IP
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE":       "Structured Adventures API",
    "DESCRIPTION": "Tanzania tour operator API — tours, guides, destinations, reviews.",
    "VERSION":     "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ── Database ────────────────────────────────────────────────────────────────────
DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')
DB_NAME   = config('DB_NAME',   default=str(BASE_DIR / 'db.sqlite3'))

if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {'default': {'ENGINE': DB_ENGINE, 'NAME': DB_NAME, 'CONN_MAX_AGE': 0}}
else:
    DATABASES = {
        'default': {
            'ENGINE':   DB_ENGINE,
            'NAME':     DB_NAME,
            'USER':     config('DB_USER', default='sa_user'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST':     config('DB_HOST', default='localhost'),
            'PORT':     config('DB_PORT', default='3306'),
            'OPTIONS':  {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Africa/Nairobi'
USE_I18N      = True
USE_TZ        = True

# ── Static & media ──────────────────────────────────────────────────────────────
STATIC_URL  = config('STATIC_URL',  default='/static/')
STATIC_ROOT = config('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles'))
WHITENOISE_USE_FINDERS    = DEBUG
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_AUTOREFRESH    = DEBUG
MEDIA_URL = '/media/'

# ── Cloudinary ──────────────────────────────────────────────────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=None),
    'API_KEY':    config('CLOUDINARY_API_KEY',    default=None),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=None),
}
if all(CLOUDINARY_STORAGE.values()):
    STORAGES = {
        "default":    {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
        "staticfiles":{"BACKEND": STATICFILES_STORAGE_BACKEND},
    }
    try:
        import cloudinary
        cloudinary.config(**CLOUDINARY_STORAGE)
    except Exception:
        pass
else:
    STORAGES = {
        "default":    {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles":{"BACKEND": STATICFILES_STORAGE_BACKEND},
    }
    MEDIA_ROOT = BASE_DIR / 'media'

# ── Email ───────────────────────────────────────────────────────────────────────
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
if EMAIL_HOST_USER:
    EMAIL_BACKEND  = config('EMAIL_BACKEND',  default='django.core.mail.backends.smtp.EmailBackend')
    EMAIL_HOST     = config('EMAIL_HOST',     default='smtp.gmail.com')
    EMAIL_PORT     = config('EMAIL_PORT',     default=587, cast=int)
    EMAIL_USE_TLS  = config('EMAIL_USE_TLS',  default=True, cast=bool)
    EMAIL_USE_SSL  = config('EMAIL_USE_SSL',  default=False, cast=bool)
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    EMAIL_TIMEOUT  = 30
    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        EMAIL_USE_SSL = False
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST    = 'localhost'
    EMAIL_PORT    = 1025
    EMAIL_USE_TLS = False
    EMAIL_TIMEOUT = 10

SITE_NAME   = config('SITE_NAME',   default='Structured Adventures')
SITE_DOMAIN = config('SITE_DOMAIN', default='structuredadventures.com')

_from = f"Structured Adventures <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else \
        f"Structured Adventures <info@structuredadventures.com>"
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=_from)
SERVER_EMAIL       = config('SERVER_EMAIL', default=f'info@{SITE_DOMAIN}')

WHATSAPP_NUMBER = config('WHATSAPP_NUMBER', default='+255741788255')
TIKTOK_HANDLE   = config('TIKTOK_HANDLE',  default='@structuredadventures')

# Staff emails — comma-separated list who receive booking/enquiry notifications
STAFF_EMAILS  = config('STAFF_EMAILS',  default='info@structuredadventures.com', cast=Csv())
CONTACT_EMAIL = config('CONTACT_EMAIL', default=f'info@{SITE_DOMAIN}')
ADMINS = [('SA Admin', e) for e in STAFF_EMAILS]

# ── DPO (offline only — no API calls from Django) ───────────────────────────────
# Staff log in to https://merchant.dpo.group/ to generate payment links manually.
# Paste the URL into the booking admin record, then use the admin action to email client.
DPO_COMPANY_TOKEN      = config('DPO_COMPANY_TOKEN', default='')
DPO_MERCHANT_DASHBOARD = 'https://merchant.dpo.group/'

# ── Google Indexing ──────────────────────────────────────────────────────────────
GOOGLE_INDEXING_ENABLED            = config('GOOGLE_INDEXING_ENABLED',          default=False, cast=bool)
GOOGLE_INDEXING_CREDENTIALS_PATH   = config('GOOGLE_INDEXING_CREDENTIALS_PATH', default='')
GOOGLE_INDEXING_AUTO_ENABLED       = config('GOOGLE_INDEXING_AUTO_ENABLED',     default=False, cast=bool)
GOOGLE_INDEXING_DAILY_QUOTA        = config('GOOGLE_INDEXING_DAILY_QUOTA',      default=200, cast=int)

# ── Cache ────────────────────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(BASE_DIR / 'tmp' / 'django_cache'),
        'TIMEOUT': 600,
        'OPTIONS': {'MAX_ENTRIES': 3000},
    }
}

SESSION_ENGINE         = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE     = 86400 * 30
SESSION_SAVE_EVERY_REQUEST = False

# ── Logging ──────────────────────────────────────────────────────────────────────
LOG_DIR = BASE_DIR / 'logs'
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name} {module}:{lineno} — {message}', 'style': '{', 'datefmt': '%Y-%m-%d %H:%M:%S'},
        'simple':  {'format': '[{asctime}] {levelname} — {message}',                          'style': '{', 'datefmt': '%Y-%m-%d %H:%M:%S'},
    },
    'handlers': {
        'console':   {'class': 'logging.StreamHandler', 'formatter': 'simple', 'level': 'INFO'},
        'app_file':  {'class': 'logging.handlers.TimedRotatingFileHandler', 'filename': str(LOG_DIR / 'django.log'), 'when': 'midnight', 'backupCount': 30, 'encoding': 'utf-8', 'formatter': 'verbose', 'level': 'INFO'},
        'error_file':{'class': 'logging.handlers.TimedRotatingFileHandler', 'filename': str(LOG_DIR / 'error.log'),  'when': 'midnight', 'backupCount': 60, 'encoding': 'utf-8', 'formatter': 'verbose', 'level': 'ERROR'},
        'mail_file': {'class': 'logging.handlers.TimedRotatingFileHandler', 'filename': str(LOG_DIR / 'mail.log'),   'when': 'midnight', 'backupCount': 30, 'encoding': 'utf-8', 'formatter': 'verbose', 'level': 'INFO'},
    },
    'loggers': {
        'django':                       {'handlers': ['console', 'app_file', 'error_file'], 'level': 'INFO',  'propagate': False},
        'django.request':               {'handlers': ['console', 'app_file', 'error_file'], 'level': 'WARNING','propagate': False},
        'apps.booking':                 {'handlers': ['console', 'app_file', 'error_file'], 'level': 'INFO',  'propagate': False},
        'apps.core.services.email_service': {'handlers': ['console', 'mail_file', 'error_file'], 'level': 'INFO', 'propagate': False},
        'apps':                         {'handlers': ['console', 'app_file', 'error_file'], 'level': 'INFO',  'propagate': False},
    },
    'root': {'handlers': ['console', 'app_file', 'error_file'], 'level': 'INFO'},
}

# ── CKEditor ─────────────────────────────────────────────────────────────────────
CKEDITOR_5_CONFIGS = {
    'default': {'toolbar': ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote']},
    'extends': {
        'blockToolbar': ['paragraph', 'heading1', 'heading2', 'heading3', '|', 'bulletedList', 'numberedList', 'todoList'],
        'toolbar': ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote', 'imageUpload'],
    }
}

# ── Unfold admin theme ────────────────────────────────────────────────────────────
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE":     "Structured Adventures",
    "SITE_HEADER":    "Structured Adventures",
    "SITE_SUBHEADER": "Content & Booking Management",
    "SITE_URL":       "/",
    "SITE_SYMBOL":    "landscape",
    "SHOW_HISTORY":   True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON":  True,
    "ENVIRONMENT": "apps.core.admin_unfold.environment_callback",
    "COLORS": {
        "primary": {
            "50": "255 247 237", "100": "255 237 213", "200": "254 215 170",
            "300": "253 186 116", "400": "251 146 60",  "500": "249 115 22",
            "600": "234 88 12",   "700": "194 65 12",   "800": "154 52 18",
            "900": "124 45 18",   "950": "67 20 7",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "🥾 Tours & Bookings",
                "separator": True,
                "items": [
                    {"title": "Tours",            "icon": "hiking",               "link": reverse_lazy("admin:tours_tour_changelist")},
                    {"title": "Combo packages",   "icon": "luggage",              "link": reverse_lazy("admin:tours_combopackage_changelist")},
                    {"title": "Tour categories",  "icon": "category",             "link": reverse_lazy("admin:tours_tourcategory_changelist")},
                    {"title": "Tags",             "icon": "sell",                 "link": reverse_lazy("admin:tours_tag_changelist")},
                    {"title": "Itineraries",      "icon": "map",                  "link": reverse_lazy("admin:tours_itinerary_changelist")},
                    {"title": "Bookings",         "icon": "confirmation_number",  "link": reverse_lazy("admin:booking_booking_changelist")},
                    {"title": "Group departures", "icon": "groups",               "link": reverse_lazy("admin:booking_groupdeparture_changelist")},
                    {"title": "Contact enquiries","icon": "mail",                 "link": reverse_lazy("admin:booking_contactenquiry_changelist")},
                ],
            },
            {
                "title": "🗻 Destinations",
                "separator": True,
                "items": [
                    {"title": "Destinations", "icon": "terrain",  "link": reverse_lazy("admin:destinations_destination_changelist")},
                    {"title": "Categories",   "icon": "category", "link": reverse_lazy("admin:destinations_destinationcategory_changelist")},
                ],
            },
            {
                "title": "🧭 Guides & Blog",
                "separator": True,
                "items": [
                    {"title": "Trek guides",      "icon": "explore", "link": reverse_lazy("admin:guide_trekguide_changelist")},
                    {"title": "Blog articles",    "icon": "article", "link": reverse_lazy("admin:guide_blogarticle_changelist")},
                    {"title": "Guide categories", "icon": "category","link": reverse_lazy("admin:guide_guidecategory_changelist")},
                ],
            },
            {
                "title": "⭐ Reviews",
                "separator": True,
                "items": [
                    {"title": "Tour reviews",     "icon": "star",    "link": reverse_lazy("admin:reviews_tourreview_changelist")},
                    {"title": "External reviews", "icon": "reviews", "link": reverse_lazy("admin:reviews_externalreview_changelist")},
                ],
            },
            {
                "title": "⚙️ Site Settings",
                "separator": True,
                "items": [
                    {"title": "Site settings", "icon": "settings", "link": reverse_lazy("admin:core_sitesettings_changelist")},
                    {"title": "FAQs",          "icon": "help",     "link": reverse_lazy("admin:core_faq_changelist")},
                    {"title": "Team members",  "icon": "badge",    "link": reverse_lazy("admin:core_teammember_changelist")},
                    {"title": "Job postings",  "icon": "work",     "link": reverse_lazy("admin:core_jobposting_changelist")},
                ],
            },
            {
                "title": "🔐 Access",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Users",  "icon": "person", "link": reverse_lazy("admin:auth_user_changelist")},
                    {"title": "Groups", "icon": "group",  "link": reverse_lazy("admin:auth_group_changelist")},
                ],
            },
        ],
    },
}
