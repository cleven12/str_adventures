from django.test import TestCase
from django.urls import reverse

from apps.tours.models import Tour, TourCategory


class TourListFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = TourCategory.objects.create(name="Kilimanjaro", slug="kilimanjaro")
        safari_category = TourCategory.objects.create(name="Safari", slug="safari")

        Tour.objects.create(
            title="Machame Route 7 Days",
            category=category,
            tour_type="multi_day_trek",
            place_name="Mount Kilimanjaro",
            duration_days=7,
            difficulty="moderate",
            price_usd=2390,
            excerpt="Classic Kilimanjaro climb.",
            description="A seven day Machame route climb.",
            is_active=True,
        )
        Tour.objects.create(
            title="Serengeti Safari 5 Days",
            category=safari_category,
            tour_type="safari",
            place_name="Serengeti National Park",
            duration_days=5,
            difficulty="easy",
            price_usd=1890,
            excerpt="Classic safari.",
            description="A five day Tanzania safari.",
            is_active=True,
        )

    def test_search_and_type_filter_return_the_expected_tour(self):
        response = self.client.get(
            reverse("tours:tour_list"),
            {"q": "machame", "type": "multi_day_trek"},
        )

        self.assertContains(response, "Machame Route 7 Days")
        self.assertNotContains(response, "Serengeti Safari 5 Days")

    def test_filter_and_sort_controls_keep_the_query_state(self):
        response = self.client.get(reverse("tours:tour_list"))

        self.assertContains(response, 'id="tour-filter-form"')
        self.assertContains(
            response,
            'hx-trigger="change, keyup changed delay:500ms from:input[name=\'q\']"',
        )
        self.assertContains(response, 'id="tour-sort-form"')
        self.assertContains(response, 'hx-include="#tour-filter-form"')
        self.assertContains(response, 'name="page" value="1"')
