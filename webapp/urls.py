from django.urls import path

from . import views

app_name = "webapp"

urlpatterns = [
    path("", views.home, name="home"),
    path("restaurants/", views.restaurant_list, name="restaurant_list"),
    path("restaurants/<int:pk>/", views.restaurant_detail, name="restaurant_detail"),
    path("restaurants/<int:pk>/favorite/", views.set_favorite, name="set_favorite"),
    path("favorites/", views.favorite_list, name="favorite_list"),
    path("roulette/", views.roulette, name="roulette"),
    path("roulette/result/", views.roulette_result, name="roulette_result"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("users/<int:user_id>/", views.profile, name="profile"),
    path("users/<int:user_id>/follow/", views.follow_toggle, name="follow_toggle"),
    path("users/<int:user_id>/followers/", views.follow_list, {"kind": "followers"}, name="followers"),
    path("users/<int:user_id>/following/", views.follow_list, {"kind": "following"}, name="following"),
    path("restaurants/<int:restaurant_id>/reviews/", views.review_list, name="review_list"),
    path("restaurants/<int:restaurant_id>/reviews/create/", views.review_create, name="review_create"),
    path("reviews/<int:review_id>/edit/", views.review_update, name="review_update"),
    path("reviews/<int:review_id>/delete/", views.review_delete, name="review_delete"),
]
