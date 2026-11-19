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
    # Django �������� ���ѡ�CSRF �˻�� ���� ���� �״�� ����մϴ�.
    # ������ ���� ȭ�鿡�� ����� �޴��� �Բ� ��ϡ������� �� �ֽ��ϴ�.
    inlines = [MenuInline]


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "price")
    search_fields = ("name", "restaurant__name")
    list_filter = ("restaurant__category",)
    list_select_related = ("restaurant",)
