"""
Public SEO surface tests for CI (robots, sitemap, key landing pages).
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse


@override_settings(
    ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'],
    SITE_DOMAIN='v2.visitkili.com',
)
class SEOPublicSurfaceTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_robots_txt(self):
        response = self.client.get(reverse('core:robots'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('User-agent: *', body)
        self.assertIn('Sitemap:', body)
        self.assertIn('sitemap.xml', body)

    def test_sitemap_xml_valid_shell(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertIn('xml', response['Content-Type'])
        body = response.content.decode()
        self.assertIn('<?xml', body)
        self.assertIn('<urlset', body)
        # Static URLs should appear even with empty content DB
        self.assertIn('<loc>', body)

    def test_home_ok(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    def test_contact_get_ok(self):
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)

    def test_tour_list_ok(self):
        response = self.client.get(reverse('tours:tour_list'))
        self.assertEqual(response.status_code, 200)

    def test_destinations_list_ok(self):
        response = self.client.get(reverse('destinations:list'))
        self.assertEqual(response.status_code, 200)

    def test_guides_list_ok(self):
        response = self.client.get(reverse('guide:guide_list'))
        self.assertEqual(response.status_code, 200)

    def test_home_has_basic_meta_or_title(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode().lower()
        self.assertIn('<title', body)
        # Prefer explicit meta description when present
        self.assertTrue(
            'meta name="description"' in body
            or 'meta property="og:title"' in body
            or 'visit kili' in body
        )
