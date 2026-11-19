from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from .models import Menu, Restaurant


class HomePageTests(SimpleTestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("webapp:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "���ָ���")


class RestaurantFeatureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cheap = Restaurant.objects.create(
            name="�ܰ� �Ĵ�", category=Restaurant.Category.JAPANESE,
            district="�ܰ赿", address="���ֽ� �ܰ赿",
        )
        cls.expensive = Restaurant.objects.create(
            name="��� �Ĵ�", category=Restaurant.Category.JAPANESE,
            district="�����", address="���ֽ� �����",
        )
        Menu.objects.bulk_create([
            Menu(restaurant=cls.cheap, name="������", price=11_500),
            Menu(restaurant=cls.cheap, name="ġ�� ������", price=12_000),
            Menu(restaurant=cls.expensive, name="������", price=15_000),
            Menu(restaurant=cls.expensive, name="�쵿", price=7_000),
        ])

    def test_menu_keyword_and_price_match_same_row_without_duplicate_restaurants(self):
        response = self.client.get(reverse("webapp:restaurant_list"), {
            "keyword": "������", "category": "japanese", "max_price": "12000",
        })
        self.assertEqual(list(response.context["restaurants"]), [self.cheap])

    def test_restaurant_name_district_and_invalid_filter(self):
        url = reverse("webapp:restaurant_list")
        response = self.client.get(url, {"keyword": "��� �Ĵ�", "district": "���"})
        self.assertEqual(list(response.context["restaurants"]), [self.expensive])
        invalid = self.client.get(url, {"max_price": "-1"})
        self.assertIn("max_price", invalid.context["form"].errors)
        self.assertFalse(invalid.context["restaurants"])

    def test_detail_shows_own_menus_only_and_unknown_restaurant_is_404(self):
        response = self.client.get(reverse("webapp:restaurant_detail", args=[self.cheap.pk]))
        self.assertContains(response, "ġ�� ������")
        self.assertNotContains(response, "�쵿")
        missing = self.client.get(reverse("webapp:restaurant_detail", args=[99999]))
        self.assertEqual(missing.status_code, 404)

    def test_roulette_shows_exact_menu_sellers_in_selected_category(self):
        other = Restaurant.objects.create(
            name="�н���", category=Restaurant.Category.SNACK,
            district="�߾ӵ�", address="���ֽ� �߾ӵ�",
        )
        Menu.objects.create(restaurant=other, name="������", price=8000)
        with patch("webapp.views.choice", side_effect=["japanese", "������"]):
            response = self.client.post(reverse("webapp:roulette"))
        self.assertEqual(response.context["selected_menu"], "������")
        self.assertEqual({menu.restaurant_id for menu in response.context["sellers"]},
                         {self.cheap.pk, self.expensive.pk})
        self.assertNotContains(response, "�н���")

    def test_roulette_empty_state_and_csrf(self):
        Menu.objects.all().delete()
        url = reverse("webapp:roulette")
        self.assertContains(self.client.post(url), "���� ��õ�� �޴��� �����.")
        self.assertEqual(Client(enforce_csrf_checks=True).post(url).status_code, 403)

    def test_admin_crud_updates_public_results(self):
        admin_add = reverse("admin:webapp_restaurant_add")
        payload = {
            "name": "�ݰ� �׽�Ʈ �Ĵ�", "category": "western", "district": "�ݰ",
            "address": "���ֽ� �ݰ", "menus-TOTAL_FORMS": 1,
            "menus-INITIAL_FORMS": 0, "menus-0-name": "ũ�� �Ľ�Ÿ",
            "menus-0-price": 12_000, "_save": "1",
        }
        self.assertEqual(self.client.post(admin_add, payload).status_code, 302)
        self.assertFalse(Restaurant.objects.filter(name=payload["name"]).exists())
        users = get_user_model().objects
        self.client.force_login(users.create_user(username="staff", is_staff=True))
        self.assertEqual(self.client.post(admin_add, payload).status_code, 403)

        self.client.force_login(users.create_superuser(username="manager"))
        self.assertEqual(self.client.post(admin_add, payload).status_code, 302)
        restaurant = Restaurant.objects.get(name=payload["name"])
        menu = restaurant.menus.get()
        search_url = reverse("webapp:restaurant_list")
        query = {"keyword": "ũ�� �Ľ�Ÿ", "max_price": "13000"}
        self.assertContains(self.client.get(search_url, query), restaurant.name)
        update = reverse("admin:webapp_menu_change", args=[menu.pk])
        self.assertEqual(self.client.post(update, {
            "restaurant": restaurant.pk, "name": menu.name, "price": 14_000, "_save": "1",
        }).status_code, 302)
        self.assertNotContains(self.client.get(search_url, query), restaurant.name)

        delete = reverse("admin:webapp_restaurant_delete", args=[restaurant.pk])
        self.assertEqual(self.client.get(delete).status_code, 200)
        self.assertTrue(Restaurant.objects.filter(pk=restaurant.pk).exists())
        self.assertEqual(self.client.post(delete, {"post": "yes"}).status_code, 302)
        self.assertFalse(Restaurant.objects.filter(pk=restaurant.pk).exists())
        self.assertFalse(Menu.objects.filter(pk=menu.pk).exists())
