from time import time

from django.db.models import F
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.crypto import salted_hmac
from django.utils.deprecation import MiddlewareMixin

from .models import LoginAttemptWindow


class MultipartSizeLimitMiddleware(MiddlewareMixin):
    MAX_REQUEST_BYTES = 6 * 1024 * 1024

    def process_request(self, request):
        if request.content_type != "multipart/form-data":
            return None
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("잘못된 요청 크기입니다.")
        if length < 0:
            return HttpResponseBadRequest("잘못된 요청 크기입니다.")
        # 본문 길이가 제공되면 Django가 폼을 파싱하기 전에 거절합니다.
        if length > self.MAX_REQUEST_BYTES:
            return HttpResponse("업로드 요청이 너무 큽니다.", status=413)
        return None


class LoginRateLimitMiddleware(MiddlewareMixin):
    WINDOW_SECONDS = 300
    LIMITS = {"webapp:login": 12, "admin:login": 8}

    def process_view(self, request, view_func, view_args, view_kwargs):
        route = request.resolver_match.view_name
        limit = self.LIMITS.get(route)
        if request.method != "POST" or limit is None:
            return None

        # 클라이언트가 전달한 프록시 헤더 대신 서버가 알려 준 주소만 사용합니다.
        address = request.META.get("REMOTE_ADDR") or "unknown"
        key = salted_hmac("matpick-login-attempt", f"{route}:{address}", algorithm="sha256").hexdigest()
        now = int(time())
        window = now - now % self.WINDOW_SECONDS

        bucket, created = LoginAttemptWindow.objects.get_or_create(key=key, window_start=window)
        if created:
            LoginAttemptWindow.objects.filter(window_start__lt=window).delete()

        # DB에서 한 번에 비교하고 증가시켜 서로 다른 프로세스에도 같은 제한을 적용합니다.
        allowed = LoginAttemptWindow.objects.filter(pk=bucket.pk, attempts__lt=limit).update(
            attempts=F("attempts") + 1
        )
        if allowed:
            return None

        return HttpResponse(
            "로그인 요청이 너무 많습니다. 잠시 뒤 다시 시도해 주세요.",
            status=429,
            content_type="text/plain; charset=utf-8",
            headers={"Retry-After": str(window + self.WINDOW_SECONDS - now), "Cache-Control": "no-store"},
        )
