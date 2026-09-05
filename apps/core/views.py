# apps/core/views.py — Structured Adventures
# API-only backend: no page-rendering views live here any more. Only the
# error handlers remain, wired up via handler400/403/404/500 in config/urls.py
# and CSRF_FAILURE_VIEW in config/settings.py — both need real callables
# regardless of there being no HTML to render.
from django.http import JsonResponse


def custom_400(request, exception=None):
    return JsonResponse({"detail": "Bad request."}, status=400)


def custom_403(request, exception=None):
    return JsonResponse({"detail": "Forbidden."}, status=403)


def custom_404(request, exception=None):
    return JsonResponse({"detail": "Not found."}, status=404)


def custom_500(request):
    return JsonResponse({"detail": "Internal server error."}, status=500)


def custom_csrf_failure(request, reason=""):
    return JsonResponse({"detail": "CSRF verification failed."}, status=403)
