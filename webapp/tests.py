from django.test import SimpleTestCase
from django.urls import reverse


class HomePageTests(SimpleTestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("webapp:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "원주맛픽")
