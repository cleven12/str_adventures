# config/api_settings.py
# Add these to your existing config/settings.py
# ─────────────────────────────────────────────

# 1. Add to INSTALLED_APPS (THIRD_PARTY_APPS list):
#    'rest_framework',
#    'django_filters',
#    'drf_spectacular',
#    'corsheaders',

# 2. Add to MIDDLEWARE (BEFORE SessionMiddleware):
#    'corsheaders.middleware.CorsMiddleware',

# 3. Paste these settings blocks:

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",                        # Next.js dev
    "https://structuredadventures.com",             # production
    "https://www.structuredadventures.com",
]
CORS_ALLOW_CREDENTIALS = False  # API is public read — no cookies needed

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

# Cache — use Redis in production; file cache for dev
CACHES = {
    "default": {
        "BACKEND":  "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(BASE_DIR / "tmp" / "django_cache"),
        "TIMEOUT":  600,
        "OPTIONS":  {"MAX_ENTRIES": 5000},
    }
}

# Production: switch to Redis
# CACHES = {
#     "default": {
#         "BACKEND":  "django.core.cache.backends.redis.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "TIMEOUT":  600,
#     }
# }
