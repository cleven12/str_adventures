# apps/reviews/api_views.py
# Write endpoint for tour reviews — ported from apps/reviews/views.py's
# submit_review logic. The original required a logged-in user with a
# confirmed booking; this API has no user-auth system, so the booking's
# own secure_token (already used for booking/group-join confirmation links)
# takes the place of login as proof the reviewer actually booked.

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.booking.models import Booking
from apps.tours.models import Tour
from .forms import TourReviewForm


class TourReviewCreateView(APIView):
    """POST /api/v1/tours/<slug>/reviews/ — {booking_secure_token, rating, title, body, travel_date}"""

    def post(self, request, slug):
        tour = get_object_or_404(Tour, slug=slug, is_active=True)

        token = (request.data.get("booking_secure_token") or "").strip()
        if not token:
            return Response({"detail": "booking_secure_token is required."}, status=400)

        booking = Booking.objects.filter(
            tour=tour,
            secure_token=token,
            status__in=["confirmed", "completed"],
            payment_confirmed=True,
        ).first()
        if not booking:
            return Response(
                {"detail": "No confirmed, paid booking found for this tour and token."},
                status=403,
            )
        if hasattr(booking, "review"):
            return Response(
                {"detail": "You have already reviewed this booking."}, status=409
            )

        form = TourReviewForm(request.data)
        if not form.is_valid():
            return Response({"errors": form.errors}, status=400)

        review = form.save(commit=False)
        review.tour = tour
        review.booking = booking
        review.name = booking.full_name
        review.email = booking.email
        review.save()

        return Response(
            {"detail": "Thank you! Your review has been submitted for moderation."},
            status=201,
        )
