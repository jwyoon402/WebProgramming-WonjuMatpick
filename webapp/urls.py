"""Application URLs. Agree on URL names before implementing screens."""
from django.urls import path
from . import views

app_name = "webapp"

urlpatterns = [
    path("", views.home, name="home"),
]
