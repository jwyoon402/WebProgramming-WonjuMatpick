from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import transaction
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image, PngImagePlugin

from .forms import ReviewPhotoField
from .middleware import LoginRateLimitMiddleware, MultipartSizeLimitMiddleware
from .models import Favorite, Follow, MemberProfile, Menu, Restaurant, Review


class HomePageTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("webapp:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "원주맛픽")


class RestaurantFeatureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cheap = Restaurant.objects.create(
            name="단계 식당", category=Restaurant.Category.JAPANESE,
            district="단계동", address="원주시 단계동",
        )
        cls.expensive = Restaurant.objects.create(
            name="흥업 식당", category=Restaurant.Category.JAPANESE,
            district="흥업면", address="원주시 흥업면",
        )
        Menu.objects.bulk_create([
            Menu(restaurant=cls.cheap, name="돈가스", price=11_500),
            Menu(restaurant=cls.cheap, name="치즈 돈가스", price=12_000),
            Menu(restaurant=cls.expensive, name="돈가스", price=15_000),
            Menu(restaurant=cls.expensive, name="우동", price=7_000),
        ])

    def test_menu_keyword_and_price_match_same_row_without_duplicate_restaurants(self):
        response = self.client.get(reverse("webapp:restaurant_list"), {
            "keyword": "돈가스", "category": "japanese", "max_price": "12000",
        })
        self.assertEqual(list(response.context["restaurants"]), [self.cheap])

    def test_restaurant_name_district_and_invalid_filter(self):
        url = reverse("webapp:restaurant_list")
        response = self.client.get(url, {"keyword": "흥업 식당", "district": "흥업"})
        self.assertEqual(list(response.context["restaurants"]), [self.expensive])
        invalid = self.client.get(url, {"max_price": "-1"})
        self.assertIn("max_price", invalid.context["form"].errors)
        self.assertFalse(invalid.context["restaurants"])

    def test_detail_shows_own_menus_only_and_unknown_restaurant_is_404(self):
        response = self.client.get(reverse("webapp:restaurant_detail", args=[self.cheap.pk]))
        self.assertContains(response, "치즈 돈가스")
        self.assertNotContains(response, "우동")
        missing = self.client.get(reverse("webapp:restaurant_detail", args=[99999]))
        self.assertEqual(missing.status_code, 404)

    def test_roulette_shows_exact_menu_sellers_in_selected_category(self):
        other = Restaurant.objects.create(
            name="분식집", category=Restaurant.Category.SNACK,
            district="중앙동", address="원주시 중앙동",
        )
        Menu.objects.create(restaurant=other, name="돈가스", price=8000)
        with patch("webapp.views.choice", side_effect=["japanese", "돈가스"]):
            response = self.client.post(reverse("webapp:roulette"), follow=True)
        self.assertEqual(response.redirect_chain, [(reverse("webapp:roulette_result"), 302)])
        self.assertEqual(response.context["selected_menu"], "돈가스")
        self.assertEqual({menu.restaurant_id for menu in response.context["sellers"]},
                         {self.cheap.pk, self.expensive.pk})
        self.assertNotContains(response, "분식집")

    def test_roulette_empty_state_and_csrf(self):
        Menu.objects.all().delete()
        url = reverse("webapp:roulette")
        self.assertRedirects(self.client.get(reverse("webapp:roulette_result")), url)
        self.assertContains(self.client.post(url, follow=True), "지금 추천할 메뉴가 없어요.")
        self.assertEqual(Client(enforce_csrf_checks=True).post(url).status_code, 403)

    def test_admin_crud_updates_public_results(self):
        admin_add = reverse("admin:webapp_restaurant_add")
        payload = {
            "name": "반곡 테스트 식당", "category": "western", "district": "반곡동",
            "address": "원주시 반곡동", "menus-TOTAL_FORMS": 1,
            "menus-INITIAL_FORMS": 0, "menus-0-name": "크림 파스타",
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
        query = {"keyword": "크림 파스타", "max_price": "13000"}
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


    def test_search_filters_by_actual_review_average(self):
        first = get_user_model().objects.create_user(username="first-rater")
        second = get_user_model().objects.create_user(username="second-rater")
        Review.objects.create(restaurant=self.cheap, author=first, rating=5, content="Great")
        Review.objects.create(restaurant=self.cheap, author=second, rating=3, content="Good")
        url = reverse("webapp:restaurant_list")
        response = self.client.get(url, {"min_rating": "4.0"})
        self.assertEqual(list(response.context["restaurants"]), [self.cheap])
        response = self.client.get(url, {"min_rating": "4.1"})
        self.assertFalse(response.context["restaurants"])

    def test_favorites_require_login_and_repeated_adds_create_one_row(self):
        user = get_user_model().objects.create_user(username="favorite-owner")
        other = get_user_model().objects.create_user(username="other-owner")
        Favorite.objects.create(user=other, restaurant=self.expensive)
        url = reverse("webapp:set_favorite", args=[self.cheap.pk])
        self.assertEqual(self.client.post(url, {"action": "add"}).status_code, 302)
        self.assertFalse(Favorite.objects.filter(user=user).exists())
        self.client.force_login(user)
        self.assertEqual(self.client.get(url).status_code, 405)
        for _ in range(2):
            self.assertEqual(self.client.post(url, {"action": "add"}).status_code, 302)
        self.assertEqual(Favorite.objects.filter(user=user).count(), 1)
        response = self.client.get(reverse("webapp:favorite_list"))
        self.assertEqual(list(response.context["restaurants"]), [self.cheap])
        self.client.post(url, {"action": "remove"})
        self.assertFalse(Favorite.objects.filter(user=user).exists())
        self.assertTrue(Favorite.objects.filter(user=other).exists())


User = get_user_model()


class UserFeatureTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="테스트 식당", category=Restaurant.Category.KOREAN,
            district="무실동", address="테스트 주소")

    def test_signup_creates_nickname_and_prompts_login(self):
        response = self.client.post(reverse("webapp:signup"), {
            "username": "tester", "nickname": "테스트별명", "email": "test@example.com",
            "password1": "StrongPass!123", "password2": "StrongPass!123",
        })
        self.assertRedirects(response, reverse("webapp:login"))
        self.assertEqual(MemberProfile.objects.get(user__username="tester").nickname, "테스트별명")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(username="first", email="test@example.com", password="StrongPass!123")
        response = self.client.post(reverse("webapp:signup"), {
            "username": "second", "nickname": "두 번째", "email": "TEST@example.com",
            "password1": "StrongPass!123", "password2": "StrongPass!123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="second").exists())

    def test_login_valid_credentials(self):
        user = User.objects.create_user(username="loginuser", password="StrongPass!123")
        response = self.client.post(reverse("webapp:login"), {"username": "loginuser", "password": "StrongPass!123"})
        self.assertRedirects(response, reverse("webapp:home"))
        self.assertEqual(int(self.client.session.get("_auth_user_id")), user.pk)

    def test_login_invalid_credentials(self):
        User.objects.create_user(username="loginuser", password="StrongPass!123")
        response = self.client.post(reverse("webapp:login"), {"username": "loginuser", "password": "wrong-password"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get("_auth_user_id"))
        self.assertTrue(response.context["form"].errors)

    def test_logout_requires_post_and_clears_session(self):
        User.objects.create_user(username="logoutuser", password="StrongPass!123")
        self.client.login(username="logoutuser", password="StrongPass!123")
        self.assertEqual(self.client.get(reverse("webapp:logout")).status_code, 405)
        response = self.client.post(reverse("webapp:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_profile_shows_counts(self):
        user = User.objects.create_user(username="profileuser", password="password123")
        response = self.client.get(reverse("webapp:profile", args=[user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profileuser")
        self.assertEqual(response.context["followers_count"], 0)
        self.assertEqual(response.context["following_count"], 0)

    def test_review_create_and_read(self):
        author = User.objects.create_user(username="reviewer", password="password123")
        self.client.login(username="reviewer", password="password123")
        response = self.client.post(reverse("webapp:review_create", args=[self.restaurant.pk]), {"rating": 5, "content": "맛있어요"})
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get()
        self.assertEqual(review.author, author)
        self.assertEqual(review.restaurant, self.restaurant)
        self.assertContains(self.client.get(reverse("webapp:review_list", args=[self.restaurant.pk])), "맛있어요")

    def test_review_create_requires_login(self):
        response = self.client.post(reverse("webapp:review_create", args=[self.restaurant.pk]), {"rating": 4, "content": "review"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.exists())

    def test_review_edit_only_author(self):
        author = User.objects.create_user(username="author", password="password123")
        other = User.objects.create_user(username="other", password="password123")
        review = Review.objects.create(restaurant=self.restaurant, author=author, rating=3, content="old")
        self.client.login(username="other", password="password123")
        response = self.client.post(reverse("webapp:review_update", args=[review.pk]), {"rating": 5, "content": "unauthorized"})
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.content, "old")
        self.client.logout()
        self.client.login(username="author", password="password123")
        response = self.client.post(reverse("webapp:review_update", args=[review.pk]), {"rating": 4, "content": "updated"})
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.content, "updated")
        self.assertEqual(review.rating, 4)

    def test_review_delete_only_author_and_post_only(self):
        author = User.objects.create_user(username="author", password="password123")
        other = User.objects.create_user(username="other", password="password123")
        review = Review.objects.create(restaurant=self.restaurant, author=author, rating=4, content="keep")
        self.client.login(username="other", password="password123")
        self.assertEqual(self.client.get(reverse("webapp:review_delete", args=[review.pk])).status_code, 405)
        self.client.post(reverse("webapp:review_delete", args=[review.pk]))
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())
        self.client.logout()
        self.client.login(username="author", password="password123")
        self.client.post(reverse("webapp:review_delete", args=[review.pk]))
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_follow_toggle_and_no_self_follow(self):
        a = User.objects.create_user(username="a", password="password123")
        b = User.objects.create_user(username="b", password="password123")
        self.client.login(username="a", password="password123")
        url = reverse("webapp:follow_toggle", args=[b.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertTrue(Follow.objects.filter(follower=a, following=b).exists())
        self.client.post(url)
        self.assertFalse(Follow.objects.filter(follower=a, following=b).exists())
        self.client.post(reverse("webapp:follow_toggle", args=[a.pk]))
        self.assertFalse(Follow.objects.filter(follower=a, following=a).exists())

    def test_follow_lists(self):
        a = User.objects.create_user(username="follower", password="password123")
        b = User.objects.create_user(username="target", password="password123")
        Follow.objects.create(follower=a, following=b)
        self.assertContains(self.client.get(reverse("webapp:followers", args=[b.pk])), "follower")
        self.assertContains(self.client.get(reverse("webapp:following", args=[a.pk])), "target")

    def test_review_appears_on_restaurant_detail(self):
        user = User.objects.create_user(username="diner")
        Review.objects.create(
            restaurant=self.restaurant, author=user, rating=4, content="Detail review",
        )
        response = self.client.get(reverse("webapp:restaurant_detail", args=[self.restaurant.pk]))
        self.assertContains(response, "Detail review")
        self.assertEqual(response.context["review_count"], 1)
        self.assertEqual(response.context["average_rating"], 4.0)

    def test_login_returns_to_the_review_form(self):
        user = User.objects.create_user(username="nextuser", password="StrongPass!123")
        create_url = reverse("webapp:review_create", args=[self.restaurant.pk])
        login_response = self.client.get(create_url, follow=True)
        self.assertContains(login_response, f'name="next" value="{create_url}"')
        response = self.client.post(reverse("webapp:login"), {
            "username": user.username, "password": "StrongPass!123", "next": create_url,
        })
        self.assertRedirects(response, create_url)

    def test_follow_from_review_and_unfollow_from_filtered_list(self):
        reader = User.objects.create_user(username="reader")
        author = User.objects.create_user(username="author")
        MemberProfile.objects.create(user=author, nickname="맛집탐험")
        Review.objects.create(restaurant=self.restaurant, author=author, rating=5, content="좋았어요")
        self.client.force_login(reader)
        review_list = reverse("webapp:review_list", args=[self.restaurant.pk])
        profile = reverse("webapp:profile", args=[author.pk])
        follow = reverse("webapp:follow_toggle", args=[author.pk])
        self.assertContains(self.client.get(review_list), f'href="{profile}"')
        for _ in range(2):
            self.assertRedirects(self.client.post(follow, {"action": "follow", "next": review_list}), review_list)
        self.assertEqual(Follow.objects.filter(follower=reader, following=author).count(), 1)
        following = reverse("webapp:following", args=[reader.pk])
        response = self.client.get(following, {"q": "탐험"})
        self.assertContains(response, "맛집탐험")
        self.assertEqual(response.context["people"][0].review_count, 1)
        self.assertContains(response, 'value="unfollow"')
        self.assertNotContains(self.client.get(following, {"q": "없음"}), "맛집탐험")
        self.assertRedirects(self.client.post(follow, {"action": "unfollow", "next": following}), following)
        self.assertFalse(Follow.objects.exists())
        self.assertContains(self.client.get(profile), f'{reverse("webapp:restaurant_detail", args=[self.restaurant.pk])}?section=reviews#reviews')

    def test_review_photo_cleanup_on_replace_delete_and_rollback(self):
        author = User.objects.create_user(username="photo-author")
        self.client.force_login(author)

        def photo(name):
            buffer = BytesIO()
            Image.new("RGB", (2, 2)).save(buffer, "PNG")
            return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            create = reverse("webapp:review_create", args=[self.restaurant.pk])
            data = {"rating": 4, "content": "사진 리뷰"}
            self.assertEqual(self.client.post(create, {**data, "photo": photo("old.png")}).status_code, 302)
            review = Review.objects.get()
            storage, old = review.photo.storage, review.photo.name
            self.assertTrue(storage.exists(old))
            update = reverse("webapp:review_update", args=[review.pk])
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.client.post(update, {**data, "photo": photo("new.png")}).status_code, 302)
            self.assertFalse(storage.exists(old))
            review.refresh_from_db()
            current = review.photo.name
            with self.captureOnCommitCallbacks(execute=True):
                with self.assertRaisesMessage(ValueError, "rollback"):
                    with transaction.atomic():
                        Review.objects.filter(pk=review.pk).delete()
                        raise ValueError("rollback")
            self.assertTrue(storage.exists(current))
            delete = reverse("webapp:review_delete", args=[review.pk])
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.client.post(delete).status_code, 302)
            self.assertFalse(Review.objects.exists())
            self.assertFalse(storage.exists(current))


class SeedDemoTests(TestCase):
    def test_seed_demo_loads_images_and_reviews_without_duplicates(self):
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            for _ in range(2):
                call_command("seed_demo", stdout=StringIO())
            self.assertEqual(Restaurant.objects.count(), 8)
            self.assertEqual(Menu.objects.count(), 15)
            self.assertEqual(Review.objects.count(), 8)
            self.assertFalse(Menu.objects.filter(image_url="").exists())
            for review in Review.objects.all():
                self.assertTrue(review.photo.storage.exists(review.photo.name))


class SecurityRegressionTests(TestCase):
    def test_login_limits_apply_separately_and_reset_after_window(self):
        service = reverse("webapp:login")
        admin = reverse("admin:login")
        with patch.object(LoginRateLimitMiddleware, "LIMITS", {"webapp:login": 1, "admin:login": 1}):
            with patch("webapp.middleware.time", return_value=601):
                for path in (service, admin):
                    self.assertEqual(self.client.post(path, {"username": "", "password": ""}).status_code, 200)
                    limited = self.client.post(path, {"username": "", "password": ""})
                    self.assertEqual(limited.status_code, 429)
                    self.assertEqual(limited.headers["Retry-After"], "299")
                    self.assertEqual(self.client.get(path).status_code, 200)
            with patch("webapp.middleware.time", return_value=900):
                self.assertEqual(self.client.post(service, {"username": "", "password": ""}).status_code, 200)

    def test_multipart_content_length_limit_runs_before_body_parsing(self):
        response = Client(enforce_csrf_checks=True).generic(
            "POST", reverse("webapp:signup"), b"unused",
            content_type="multipart/form-data; boundary=review-test",
            CONTENT_LENGTH=str(MultipartSizeLimitMiddleware.MAX_REQUEST_BYTES + 1),
        )
        self.assertEqual(response.status_code, 413)

    def test_review_photo_limits_and_strips_metadata(self):
        png = BytesIO()
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Description", "sample metadata")
        Image.new("RGBA", (2, 2)).save(png, "PNG", pnginfo=metadata)
        data = png.getvalue()
        field = ReviewPhotoField()
        cleaned = field.clean(SimpleUploadedFile("sample.png", data, content_type="image/png"))
        self.assertNotEqual(cleaned.name, "sample.png")
        with Image.open(cleaned) as image:
            self.assertEqual(image.mode, "RGBA")
            self.assertNotIn("Description", image.info)
        with patch.object(ReviewPhotoField, "MAX_BYTES", len(data) - 1):
            with self.assertRaises(ValidationError) as error:
                field.clean(SimpleUploadedFile("sample.png", data))
            self.assertEqual(error.exception.code, "photo_size")
        with patch.object(ReviewPhotoField, "MAX_PIXELS", 3):
            with self.assertRaises(ValidationError) as error:
                field.clean(SimpleUploadedFile("sample.png", data))
            self.assertEqual(error.exception.code, "photo_dimensions")

        gif = BytesIO()
        Image.new("RGB", (2, 2)).save(gif, "GIF")
        with self.assertRaises(ValidationError) as error:
            field.clean(SimpleUploadedFile("sample.gif", gif.getvalue()))
        self.assertEqual(error.exception.code, "photo_invalid")

