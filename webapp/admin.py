from django.contrib import admin

from .models import Menu, Restaurant


class MenuInline(admin.TabularInline):
    model = Menu
    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "district", "address")
    search_fields = ("name", "district", "address", "menus__name")
    list_filter = ("category", "district")
    # Django 관리자의 권한·CSRF 검사와 검증 폼을 그대로 사용합니다.
    # 음식점 편집 화면에서 연결된 메뉴를 함께 등록·편집할 수 있습니다.
    inlines = [MenuInline]


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "price")
    search_fields = ("name", "restaurant__name")
    list_filter = ("restaurant__category",)
    list_select_related = ("restaurant",)
