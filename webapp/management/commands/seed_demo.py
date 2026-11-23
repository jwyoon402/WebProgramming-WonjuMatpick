from pathlib import Path
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.files import File
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from ...models import Follow, MemberProfile, Menu, Restaurant, Review


class Command(BaseCommand):
    help = "시연용 음식점, 메뉴 이미지, 계정 및 리뷰를 준비합니다."

    def add_arguments(self, parser):
        parser.add_argument("--base-url", default="http://127.0.0.1:8000")

    @transaction.atomic
    def handle(self, *args, **options):
        base_url = options["base_url"].rstrip("/")
        origin = urlsplit(base_url)
        if origin.scheme not in {"http", "https"} or not origin.hostname or origin.path or origin.query or origin.fragment:
            raise CommandError("--base-url에는 http://127.0.0.1:8000처럼 사이트 주소만 입력하세요.")

        # 기존 음식점이 있을 때 fixture의 고정 PK로 데이터를 덮어쓰지 않습니다.
        if not Restaurant.objects.exists():
            call_command("loaddata", "demo_restaurants", verbosity=0, stdout=self.stdout)
        demo_places = Restaurant.objects.filter(address__endswith=" (시연용)")
        if not demo_places.exists():
            raise CommandError("시연용 음식점이 없습니다. 빈 시연 DB에서 실행해 주세요.")

        static_url = f"{base_url}/static/demo"
        for restaurant in demo_places:
            updated_fields = []
            if not restaurant.image_url:
                restaurant.image_url = f"{static_url}/storefront.png"
                updated_fields.append("image_url")
            if not restaurant.phone:
                restaurant.phone = "000-0000-0000 (시연용)"
                updated_fields.append("phone")
            if updated_fields:
                restaurant.save(update_fields=updated_fields)
            Menu.objects.filter(restaurant=restaurant, image_url="").update(
                image_url=f"{static_url}/{restaurant.category}.png"
            )

        user_model = get_user_model()
        reviewers = []
        for username, nickname in (("matpick_demo_lunch", "원주점심"), ("matpick_demo_menu", "메뉴기록")):
            email = f"{username}@example.invalid"
            member = user_model.objects.filter(username=username).first()
            if member is None:
                member = user_model.objects.create_user(username=username, email=email)
            elif member.email != email or member.has_usable_password():
                raise CommandError(f"시연 계정 아이디가 기존 계정과 겹칩니다: {username}")
            MemberProfile.objects.get_or_create(user=member, defaults={"nickname": nickname})
            reviewers.append(member)

        # 로그인 가능한 공용 비밀번호 없이 샘플 프로필과 리뷰를 열어 볼 수 있게 합니다.
        Follow.objects.get_or_create(follower=reviewers[0], following=reviewers[1])
        for index, restaurant in enumerate(demo_places):
            author = reviewers[index % len(reviewers)]
            content = "메뉴 가격과 음식점 정보를 확인할 수 있어 편했어요. (발표 시연용 가상 리뷰)"
            if not Review.objects.filter(restaurant=restaurant, author=author, content=content).exists():
                image_path = finders.find(f"demo/{restaurant.category}.png")
                if not image_path:
                    raise CommandError(f"시연 이미지가 없습니다: {restaurant.category}")
                review = Review(restaurant=restaurant, author=author, rating=4 + index % 2, content=content)
                with Path(image_path).open("rb") as photo:
                    review.photo.save(f"demo-{restaurant.pk}.png", File(photo))
        self.stdout.write(self.style.SUCCESS("시연용 음식점·이미지·리뷰를 준비했습니다."))
