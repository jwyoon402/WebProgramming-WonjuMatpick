from django.contrib import admin

from .forms import AdminReviewForm
from .models import Follow, Menu, Restaurant, Review


class MenuInline(admin.TabularInline):
    # 음식점 폼에 연결된 메뉴를 표 형태로 표시합니다. extra는 새 메뉴를 입력할 빈 행 수입니다.
    model = Menu
    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    # 관리자 목록에서 음식점을 조회하고, 메뉴 이름이나 주소로 찾은 뒤 수정·삭제할 수 있습니다.
    list_display = ("name", "category", "district", "address")
    # menus__name은 음식점에서 Menu의 역참조를 따라가 메뉴 이름으로 음식점을 찾는 검색 항목입니다.
    search_fields = ("name", "district", "address", "menus__name")
    list_filter = ("category", "district")
    # Django 관리자의 권한·CSRF 검사와 검증 폼을 그대로 사용합니다.
    # 음식점 편집 화면에서 연결된 메뉴를 함께 등록·편집할 수 있습니다.
    inlines = [MenuInline]


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    # 음식점 편집 화면과 별도로 메뉴를 등록·조회·수정·삭제할 수 있습니다.
    list_display = ("name", "restaurant", "price")
    search_fields = ("name", "restaurant__name")
    list_filter = ("restaurant__category",)
    # 목록에 표시할 소속 음식점을 메뉴와 같은 쿼리에서 가져옵니다.
    list_select_related = ("restaurant",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # 관리자가 리뷰에 사진을 첨부해도 사용자 리뷰와 동일한 파일 검증을 거칩니다.
    form = AdminReviewForm
    list_display = ("id", "restaurant", "author", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("content", "author__username")

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    # 팔로우를 시작한 계정과 대상 계정을 각각 표시하고, 어느 쪽 아이디로도 검색할 수 있게 합니다.
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
