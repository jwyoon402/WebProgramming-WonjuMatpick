from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models


class Restaurant(models.Model):
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
            models.UniqueConstraint(fields=["restaurant", "name"], name="unique_restaurant_menu"),
            models.CheckConstraint(
                condition=models.Q(price__range=(1, 100_000_000)), name="menu_price_range"
            ),
        ]

    def __str__(self):
        return self.name
