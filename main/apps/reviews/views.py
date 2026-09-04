# apps/reviews/views.py — Structured Adventures
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TourReview, ExternalReview
from .forms import TourReviewForm
from apps.tours.models import Tour
from apps.booking.models import Booking


def _save_last_url(request):
    request.session['last_url'] = request.path


def reviews_list(request):
    _save_last_url(request)
    tour_reviews     = TourReview.objects.filter(is_approved=True)
    external_reviews = ExternalReview.objects.filter(is_active=True)
    paginator = Paginator(tour_reviews, 15)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'reviews/reviews_list.html', {
        'reviews':          page_obj,
        'page_obj':         page_obj,
        'external_reviews': external_reviews[:10],
        'meta_title':       'Guest Reviews | Structured Adventures',
        'meta_description': 'Read what our climbers and safari guests say about their experience in Tanzania.',
    })


@login_required
def submit_review(request, tour_slug):
    tour = get_object_or_404(Tour, slug=tour_slug, is_active=True)

    # Verified = user has a confirmed booking (payment_confirmed by staff)
    booking = Booking.objects.filter(
        user=request.user,
        tour=tour,
        status__in=['confirmed', 'completed'],
        payment_confirmed=True,
    ).first()

    if not booking:
        messages.error(request, "Only verified guests with a confirmed booking can review.")
        return redirect('tours:tour_detail', slug=tour_slug)

    if hasattr(booking, 'review'):
        messages.info(request, "You have already reviewed this booking.")
        return redirect('tours:tour_detail', slug=tour_slug)

    if request.method == 'POST':
        form = TourReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tour    = tour
            review.booking = booking
            review.user    = request.user
            review.name    = request.user.get_full_name() or request.user.username
            review.email   = request.user.email
            review.save()
            messages.success(request, "Thank you! Your review has been submitted for moderation.")
            return redirect('tours:tour_detail', slug=tour_slug)
    else:
        form = TourReviewForm(initial={'travel_date': booking.travel_date})

    return render(request, 'reviews/submit_review.html', {
        'form': form, 'tour': tour, 'booking': booking
    })
