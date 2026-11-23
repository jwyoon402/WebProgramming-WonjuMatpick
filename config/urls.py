"""Top-level URL routing for WonjuMatpick."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# 관리자 요청은 Django 관리자에 맡기고, 서비스 요청은 webapp의 URL 설정으로 보냅니다.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("webapp.urls")),
]

# Development-only upload serving. Use a proper media server in production.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
