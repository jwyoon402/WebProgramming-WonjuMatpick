from django.urls import path

from . import views

app_name = "webapp"

# [URL 라우팅] 브라우저의 경로를 views.py의 처리 함수에 연결합니다.
# 정수 PK가 있는 경로는 음식점·리뷰·사용자를 특정하여 ORM 조회에 사용합니다.
urlpatterns = [
    path("", views.home, name="home"),
    # 음식점 요청: GET 검색값을 폼에서 검증하고 ORM 조건으로 변환합니다.
    path("restaurants/", views.restaurant_list, name="restaurant_list"),
    path("restaurants/<int:pk>/", views.restaurant_detail, name="restaurant_detail"),
    path("restaurants/<int:pk>/favorite/", views.set_favorite, name="set_favorite"),
    path("favorites/", views.favorite_list, name="favorite_list"),
    # 룰렛 요청: POST로 추천 메뉴를 추첨하고 별도 GET에서 세션 결과를 표시합니다.
    path("roulette/", views.roulette, name="roulette"),
    path("roulette/result/", views.roulette_result, name="roulette_result"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("users/<int:user_id>/", views.profile, name="profile"),
    path("users/<int:user_id>/follow/", views.follow_toggle, name="follow_toggle"),
    path("users/<int:user_id>/followers/", views.follow_list, {"kind": "followers"}, name="followers"),
    path("users/<int:user_id>/following/", views.follow_list, {"kind": "following"}, name="following"),
    # 리뷰 변경은 로그인과 작성자 권한을 뷰에서 검증합니다.
    path("restaurants/<int:restaurant_id>/reviews/", views.review_list, name="review_list"),
    path("restaurants/<int:restaurant_id>/reviews/create/", views.review_create, name="review_create"),
    path("reviews/<int:review_id>/edit/", views.review_update, name="review_update"),
    path("reviews/<int:review_id>/delete/", views.review_delete, name="review_delete"),
]
