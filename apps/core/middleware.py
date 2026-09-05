from django.http import HttpResponsePermanentRedirect
from django.urls import reverse

class LegacyRedirectMiddleware:
    """
    Handles 301 redirects from v1 URLs to v2 structure.
    Prevents 404s and preserves SEO rankings for high-traffic paths.
    """

    REDIRECT_MAP = {
        # Aliases & Legacy Paths
        # NOTE: targets must be final destinations, not other map keys —
        # a target that's itself a key creates a 2-hop redirect chain
        # (GSC flags multi-hop redirects as a "Redirect error").
        '/guide/': '/guides/trekking-guides/',
        '/groups/': '/booking/groups/',

        # Old Tour Paths
        # (previous targets — /tours/tag/mount-kilimanjaro/, /budget-trekking/,
        #  /luxury-trekking/ — pointed at tags that don't exist, so these
        #  legacy URLs were 301-ing straight into a 404. Fixed to the tags
        #  that actually exist today.)
        '/tours/kilimanjaro/': '/tours/tag/kilimanjaro/',
        '/tours/mount-meru/': '/tours/tag/mount-meru/',
        '/tours/day-trips/': '/tours/?pillar=day_trip',

        # Guide/Info Paths
        '/guides/': '/guides/trekking-guides/',
        '/travel_guide/': '/guides/trekking-guides/',

        # Legacy Filter Paths (SEO Mesh)
        '/tours/filters/budget-kilimanjaro/': '/tours/tag/budget-kilimanjaro/',
        '/tours/filters/luxury-kilimanjaro/': '/tours/tag/luxury-safari/',

        # ── v1 tour/guide URLs with GSC ranking equity → v2 equivalents ──
        # (driven by Search Console export 2026-06-27; preserves rankings at launch.
        #  Targets verified to exist in v2. Impressions noted for priority.)
        '/tours/marangu-route-coca-cola-path-kilimanjaro/': '/tours/marangu-route-5-days-kilimanjaro-climb/',   # 385 impr (Coca-Cola = Marangu)
        '/tours/machame-route-whiskey-trail-kilimanjaro/': '/tours/7-day-machame-route-kilimanjaro/',           # 176 impr (Whiskey = Machame)
        '/tours/northern-circuit-route-complete-kilimanjaro/': '/tours/mt-kilimanjaro-8-day-northern-circuit-route/',  # 108 impr (Kili route, NOT safari)
        '/tours/5-days-kilimanjaro-marangu-route/': '/tours/marangu-route-5-days-kilimanjaro-climb/',           # 61 impr
        '/tours/rongai-route-northern-wilderness-trail/': '/tours/mt-kilimanjaro-3-day-rongai-route/',          # 51 impr, pos 6.7 (v2 lacks 6-7 day Rongai — content gap)
        '/guides/ultimate-kilimanjaro-packing-list-2026/': '/guides/articles/kilimanjaro-packing-list-gear-guide/',  # 43 impr (Kili packing, NOT safari)
        '/tours/lemosho-route-scenic-western-approach/': '/tours/lemosho-route-7-days-kilimanjaro-climb/',      # 28 impr
        '/tours/3-day-mount-meru-hiking-trip/': '/tours/mt-meru-3-day-climb-arusha/',                           # 20 impr
        '/tours/lemosho-route-7-days-kilimanjaro-climbing/': '/tours/lemosho-route-7-days-kilimanjaro-climb/',  # 18 impr
        '/tours/the-best-3-days-serengeti-migration-safari/': '/tours/3-days-serengeti-migration-safari/',      # 12 impr (deactivated dupe → real tour)
        '/tours/mt-kilimanjaro-7-day-lemosho-route/': '/tours/lemosho-route-7-days-kilimanjaro-climb/',         # 4 impr
        '/tours/mt-meru-day-hike-arusha/': '/tours/mt-meru-2-day-climb-arusha/',                                # 4 impr

        # ── TODO: resolve with director before launch (ambiguous / no v2 equivalent) ──
        # '/tours/category/kilimanjaro/'              (431 impr) -> Kilimanjaro listing/tag page?
        # '/tours/category/mount-meru/'               (370 impr) -> Mount Meru listing/tag page?
        # '/tours/filters/marangu-route/'              (65 impr) -> Marangu listing/tag?
        # '/tours/machame-route-kilimanjaro/'          (45 impr) -> 7-day flagship or 3-day Machame?
        # '/tours/kilimanjaro-day-hike-marangu-route/' (22 impr) -> create day-hike, or Marangu listing?
        # '/tours/shira-plateau-day-hike-kilimanjaro/'  (9 impr) -> no v2 equivalent (create or listing?)
        # '/tours/kilimanjaro/budget-packages/'        (2 impr) -> budget-Kilimanjaro listing (NOT safari)
        # '/tours/kilimanjaro/luxury-camping/'         (2 impr) -> luxury-Kilimanjaro listing
        # '/tours/7-days-mount-meru-climbing-machame-route/' (29 impr, pos 3.3) -> Meru+Machame combo? confirm intent
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Normalize trailing slash BEFORE checking the redirect map — every
        # map key has a trailing slash, so checking the raw path first sends
        # a no-slash legacy URL through two redirects (add slash, then map
        # lookup) instead of one straight to the final target.
        normalized = path if path.endswith('/') or '.' in path else path + '/'

        if normalized in self.REDIRECT_MAP:
            return HttpResponsePermanentRedirect(self.REDIRECT_MAP[normalized])

        if normalized != path:
            return HttpResponsePermanentRedirect(normalized)

        response = self.get_response(request)
        return response

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
import time

class RateLimitMiddleware:
    """
    Prevents abuse of sensitive endpoints like Contact, Chat, and Booking.
    Uses Django's database cache.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    # Server-to-server webhooks are already authenticated by the gateway's own
    # token/signature — they aren't an abuse vector like end-user form POSTs,
    # and rate-limiting them by IP means every customer's payment shares one
    # bucket keyed by the gateway's server IP (DPO calls back from the same
    # address for every transaction), so the limit trips after a handful of
    # unrelated payments and silently stops confirming bookings.
    EXEMPT_PATHS = ('/booking/dpo/callback/',)

    def __call__(self, request):
        if request.method == 'POST' and request.path not in self.EXEMPT_PATHS:
            path = request.path
            ip = self.get_client_ip(request)

            # Rate limit rules: (path_prefix, limit_per_hour, identifier)
            rules = [
                ('/api/v1/contact/', 3, ip, 'contact'),
                ('/ai-chat/message/', 20, request.session.session_key or ip, 'chat'),
                ('/api/v1/bookings/', 10, ip, 'booking'),
                ('/api/v1/group-departures/', 10, ip, 'group-join'),
            ]

            for prefix, limit, identifier, action in rules:
                if path.startswith(prefix):
                    cache_key = f'ratelimit:{action}:{identifier}'
                    count = cache.get(cache_key, 0)

                    if count >= limit:
                        if request.headers.get('HX-Request') or path.startswith('/ai-chat/'):
                            return JsonResponse({
                                'error': 'Rate limit exceeded. Please try again in an hour.'
                            }, status=429)
                        return HttpResponse('Rate limit exceeded. Please try again in an hour.', status=429)

                    # Increment count, expire in 1 hour
                    cache.set(cache_key, count + 1, 3600)
                    break

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SessionRedirectMiddleware:
    """
    Remembers the last URL to redirect user back after login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # If user is redirected to login, save the current path
        if response.status_code == 302 and 'login' in response.url:
            request.session['last_url'] = request.path

        return response
