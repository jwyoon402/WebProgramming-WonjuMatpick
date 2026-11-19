from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models


class Restaurant(models.Model):
    class Category(models.TextChoices):
        KOREAN = "korean", "�ѽ�"
        CHINESE = "chinese", "�߽�"
        JAPANESE = "japanese", "�Ͻ�"
        WESTERN = "western", "���"
        SNACK = "snack", "�н�"
        OTHER = "other", "��Ÿ"

    name = models.CharField("������ �̸�", max_length=120)
    category = models.CharField("ī�װ���", max_length=12, choices=Category.choices)
    district = models.CharField("����", max_length=60)
    address = models.CharField("�ּ�", max_length=255)
    phone = models.CharField("��ȭ��ȣ", max_length=30, blank=True)
    image_url = models.URLField(
        "��ǥ �̹��� URL", max_length=500, blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )
    description = models.TextField("�Ұ�", blank=True)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "������"
        verbose_name_plural = "������"

    def __str__(self):
        return self.name


class Menu(models.Model):
    MAX_PRICE = 100_000_000

    # �� �������� �޴��� restaurant.menus�� ��ȸ�մϴ�.
    # �������� �����ϸ� �� �������� �޴��� �Բ� �����˴ϴ�.
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="menus", verbose_name="������"
    )
    name = models.CharField("�޴� �̸�", max_length=120)
    price = models.PositiveIntegerField(
        "����(��)", validators=[MinValueValidator(1), MaxValueValidator(MAX_PRICE)]
    )
    image_url = models.URLField(
        "�޴� �̹��� URL", max_length=500, blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "�޴�"
        verbose_name_plural = "�޴�"
        constraints = [
            models.UniqueConstraint(fields=["restaurant", "name"], name="unique_restaurant_menu"),
            models.CheckConstraint(
                condition=models.Q(price__range=(1, 100_000_000)), name="menu_price_range"
            ),
        ]

    def __str__(self):
        return self.name
