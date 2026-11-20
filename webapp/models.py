from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models
from django.db.models import F, Q


class Restaurant(models.Model):
    # DB에는 검색과 룰렛에 공통으로 쓰는 영문 값을 저장하고 화면에는 한국어 이름을 표시합니다.
    class Category(models.TextChoices):
        KOREAN = "korean", "한식"
        CHINESE = "chinese", "중식"
        JAPANESE = "japanese", "일식"
        WESTERN = "western", "양식"
        SNACK = "snack", "분식"
        OTHER = "other", "기타"

    name = models.CharField("음식점 이름", max_length=120)
    category = models.CharField("카테고리", max_length=12, choices=Category.choices)
    district = models.CharField("지역", max_length=60)
    address = models.CharField("주소", max_length=255)
    phone = models.CharField("전화번호", max_length=30, blank=True)
    image_url = models.URLField(
        "대표 이미지 URL", max_length=500, blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )
    description = models.TextField("소개", blank=True)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "음식점"
        verbose_name_plural = "음식점"

    def __str__(self):
        return self.name


class Menu(models.Model):
    MAX_PRICE = 100_000_000

    # 한 음식점의 메뉴는 restaurant.menus로 조회합니다.
    # 음식점을 삭제하면 그 음식점의 메뉴도 함께 삭제됩니다.
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="menus", verbose_name="음식점"
    )
    name = models.CharField("메뉴 이름", max_length=120)
    price = models.PositiveIntegerField(
        "가격(원)", validators=[MinValueValidator(1), MaxValueValidator(MAX_PRICE)]
    )
    image_url = models.URLField(
        "메뉴 이미지 URL", max_length=500, blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "메뉴"
        verbose_name_plural = "메뉴"
        constraints = [
            # 같은 음식점에서는 메뉴명이 한 번만 등록됩니다. 가격 범위도 DB에 저장할 때 확인합니다.
            models.UniqueConstraint(fields=["restaurant", "name"], name="unique_restaurant_menu"),
            models.CheckConstraint(
                condition=models.Q(price__range=(1, 100_000_000)), name="menu_price_range"
            ),
        ]

    def __str__(self):
        return self.name


class Review(models.Model):
    # 리뷰는 음식점과 작성자에 연결됩니다. 음식점이 삭제되면 연결된 리뷰 행도 삭제됩니다.
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    content = models.TextField(max_length=2000)
    # 사진은 reviews/ 아래에 저장하고, DB의 이 필드에는 파일 경로를 기록합니다.
    photo = models.ImageField(upload_to="reviews/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # 특정 음식점의 리뷰를 최근 작성순으로 조회하는 상세 및 리뷰 목록을 위한 복합 인덱스입니다.
        indexes = [models.Index(fields=["restaurant", "-created_at"], name="webapp_rev_restau_created_idx")]

    def __str__(self):
        return f"{self.author} - {self.restaurant} ({self.rating}/5)"


class MemberProfile(models.Model):
    # 기존 Django 사용자 모델을 유지하면서 별도로 입력한 공개 닉네임을 저장합니다.
    # 사용자당 프로필 한 건을 연결합니다. 사용자 삭제 시 연결된 프로필도 함께 삭제됩니다.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="member_profile"
    )
    nickname = models.CharField("닉네임", max_length=30)


class Follow(models.Model):
    # follower는 팔로우를 시작한 사용자이고, following은 팔로우를 받는 사용자입니다.
    # 한 쌍의 방향을 구분하므로 두 사람이 서로 팔로우하는 관계도 각각 저장할 수 있습니다.
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_relations")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_relations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="webapp_unique_follow_pair"),
            # 자기 자신과의 팔로우는 DB 제약조건으로도 막습니다.
            models.CheckConstraint(condition=~Q(follower=F("following")), name="webapp_no_self_follow"),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="favorites")

    class Meta:
        constraints = [
            # 사용자와 음식점의 조합을 유일하게 유지해 관심 맛집의 중복 저장을 막습니다.
            models.UniqueConstraint(fields=["user", "restaurant"], name="webapp_unique_favorite"),
        ]


class LoginAttemptWindow(models.Model):
    # 로그인 경로와 접속 주소에서 만든 해시와 5분 구간의 시작 시각이 하나의 집계 행을 식별합니다.
    key = models.CharField(max_length=64)
    window_start = models.PositiveBigIntegerField(db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key", "window_start"], name="webapp_unique_login_window")
        ]
