from django.test import TestCase
from django.urls import reverse

class SEOURLSTestCase(TestCase):
    def test_robots_txt(self):
        response = self.client.get(reverse('core:robots'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('User-agent: *', response.content.decode())
        self.assertIn('Sitemap:', response.content.decode())

    def test_sitemap_xml(self):
        # The sitemap URL is in config/urls.py with a specific name
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', response.content.decode())
        self.assertIn('<urlset', response.content.decode())
