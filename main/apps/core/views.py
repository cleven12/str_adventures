# apps/core/views.py — Structured Adventures
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from .models import FAQ, JobPosting, SiteSettings, TeamMember
from apps.tours.models import Tour, TourCategory, ComboPackage
from apps.reviews.models import ExternalReview
from apps.core.services.email_service import EmailService


def _save_last_url(request):
    request.session['last_url'] = request.path


# ── Error handlers ──────────────────────────────────────────────────────────────
def custom_400(request, exception=None): return render(request, '400.html', status=400)
def custom_403(request, exception=None): return render(request, '403.html', status=403)
def custom_404(request, exception=None): return render(request, '404.html', status=404)
def custom_500(request):                 return render(request, '500.html', status=500)
def custom_csrf_failure(request, reason=""): return render(request, '403_csrf.html', status=403)


# ── Currency switcher ───────────────────────────────────────────────────────────
def switch_currency(request, currency_code):
    supported = ['USD', 'EUR', 'GBP', 'TZS']
    if currency_code.upper() in supported:
        request.session['currency'] = currency_code.upper()
        request.session.modified = True
    next_url = request.GET.get('next') or request.POST.get('next') or \
               request.META.get('HTTP_REFERER') or '/'
    if next_url.startswith('//') or (next_url.startswith('http') and
            request.get_host() not in next_url):
        next_url = '/'
    return redirect(next_url)


# ── Homepage ────────────────────────────────────────────────────────────────────
@method_decorator(cache_page(60 * 10), name='dispatch')
class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        _save_last_url(self.request)
        ctx = super().get_context_data(**kwargs)

        ctx['featured_tours'] = (
            Tour.objects.filter(is_active=True, is_featured=True)
            .select_related('category').prefetch_related('gallery')[:6]
        )
        from apps.booking.models import GroupDeparture
        ctx['featured_groups'] = (
            GroupDeparture.objects
            .filter(is_active=True, start_date__gte=timezone.now())
            .select_related('tour').order_by('start_date')[:4]
        )
        ctx['homepage_reviews'] = ExternalReview.objects.filter(
            is_active=True, is_featured=True
        )[:3]
        ctx['faqs']    = FAQ.objects.filter(is_active=True).order_by('order')[:6]
        ctx['pillars'] = [
            {'id': 'mountain', 'name': 'Mountain Trekking', 'type': 'multi_day_trek', 'icon': 'mountain'},
            {'id': 'safari',   'name': 'Wild Safari',       'type': 'safari',         'icon': 'binoculars'},
            {'id': 'beach',    'name': 'Beach Escapes',     'type': 'beach',          'icon': 'palmtree'},
        ]
        ctx['meta_title']       = 'Structured Adventures — Kilimanjaro, Safaris & Tanzania'
        ctx['meta_description'] = ('Arusha-based local experts for Kilimanjaro treks, '
                                   'Northern Tanzania safaris, and Zanzibar beach escapes. '
                                   'Structured, personal, no shortcuts.')
        return ctx


# ── About ───────────────────────────────────────────────────────────────────────
@cache_page(60 * 60)
def about(request):
    _save_last_url(request)
    team = TeamMember.objects.order_by('order')
    return render(request, 'core/about.html', {
        'team':             team,
        'meta_title':       'About Structured Adventures | Arusha-Based Local Experts',
        'meta_description': 'Meet the team behind Structured Adventures — Arusha-based guides with deep knowledge of Kilimanjaro, the Northern Circuit, and Tanzania\'s wild parks.',
    })


# ── Contact ─────────────────────────────────────────────────────────────────────
def contact(request):
    """Redirects to booking app contact view."""
    return redirect('booking:contact')


# ── FAQ ─────────────────────────────────────────────────────────────────────────
@cache_page(60 * 30)
def faq(request):
    _save_last_url(request)
    faqs     = FAQ.objects.filter(is_active=True).order_by('order')
    faq_schema = FAQ.get_faq_page_schema(faqs) if faqs else None
    return render(request, 'core/faq.html', {
        'faqs':             faqs,
        'faq_schema':       faq_schema,
        'meta_title':       'Frequently Asked Questions | Structured Adventures',
        'meta_description': 'Answers to common questions about Kilimanjaro climbs, Tanzania safaris, packing, costs, and booking.',
    })


# ── Careers ─────────────────────────────────────────────────────────────────────
def careers(request):
    _save_last_url(request)
    jobs = JobPosting.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'core/careers.html', {
        'jobs':       jobs,
        'meta_title': 'Careers | Structured Adventures',
    })


def job_apply(request, job_slug):
    from .models import JobApplication
    job = JobPosting.objects.filter(slug=job_slug, is_active=True).first()
    if not job:
        return redirect('core:careers')

    if request.method == 'POST':
        from .forms import JobApplicationForm
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.save()
            cv_file = request.FILES.get('cv')
            EmailService.send_job_application(application, cv_file=cv_file)
            messages.success(request, "Application submitted! We'll be in touch.")
            return redirect('core:careers')
    else:
        form = JobApplicationForm()

    return render(request, 'core/job_apply.html', {'job': job, 'form': form})


# ── Privacy / Terms ──────────────────────────────────────────────────────────────
@cache_page(60 * 60 * 24)
def privacy(request):
    return render(request, 'core/privacy.html', {'meta_title': 'Privacy Policy | Structured Adventures'})

@cache_page(60 * 60 * 24)
def terms(request):
    return render(request, 'core/terms.html', {'meta_title': 'Terms & Conditions | Structured Adventures'})
