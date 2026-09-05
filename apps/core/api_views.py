# apps/core/api_views.py
# Write endpoint for job applications — ported from apps/core/views.py's
# job_apply logic, JSON in/out instead of rendered templates.

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobApplication, JobPosting
from .services.email_service import EmailService


class JobApplicationCreateView(APIView):
    """POST /api/v1/careers/<job_slug>/apply/ — multipart (cv file)."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, job_slug):
        job = get_object_or_404(JobPosting, slug=job_slug, is_active=True)

        name  = (request.data.get("name") or "").strip()
        email = (request.data.get("email") or "").strip()
        cover_letter = request.data.get("cover_letter", "")
        cv = request.FILES.get("cv")

        errors = {}
        if not name:
            errors["name"] = ["This field is required."]
        if not email:
            errors["email"] = ["This field is required."]
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = ["Enter a valid email address."]
        if errors:
            return Response({"errors": errors}, status=400)

        application = JobApplication.objects.create(
            job=job, name=name, email=email, cover_letter=cover_letter, cv=cv,
        )
        EmailService.send_job_application(application, cv_file=cv)

        return Response(
            {"detail": "Application submitted! We'll be in touch."}, status=201
        )
