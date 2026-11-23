from time import time

from django.db.models import F
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.crypto import salted_hmac
from django.utils.deprecation import MiddlewareMixin

from .models import LoginAttemptWindow


# 파일 업로드를 포함할 수 있는 multipart 요청의 전체 본문 크기를 검사합니다.
class MultipartSizeLimitMiddleware(MiddlewareMixin):
    MAX_REQUEST_BYTES = 6 * 1024 * 1024

    def process_request(self, request):
        if request.content_type != "multipart/form-data":
            return None
        # 파일, 다른 폼 필드, multipart 구분자를 포함한 전체 Content-Length입니다.
        # 길이가 제공되지 않으면 이 검사에서 통과하며, 사진 폼에서 파일 자체의 크기를 별도로 확인합니다.
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


# 로그인 뷰 실행 전에 각 경로와 접속 주소별 POST 요청 횟수를 DB로 관리합니다.
class LoginRateLimitMiddleware(MiddlewareMixin):
    WINDOW_SECONDS = 300
    LIMITS = {"webapp:login": 12, "admin:login": 8}

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Django가 해석한 뷰 이름으로 일반 로그인과 관리자 로그인을 구분합니다.
        # 5분마다 일반 로그인은 12회, 관리자 로그인은 8회의 POST 요청을 허용합니다.
        route = request.resolver_match.view_name
        limit = self.LIMITS.get(route)
        if request.method != "POST" or limit is None:
            return None

        # 클라이언트가 전달한 프록시 헤더 대신 서버가 알려 준 주소만 사용합니다.
        address = request.META.get("REMOTE_ADDR") or "unknown"
        key = salted_hmac("matpick-login-attempt", f"{route}:{address}", algorithm="sha256").hexdigest()
        # 현재 시각에서 300초로 나눈 나머지를 빼 고정된 5분 구간의 시작 시각을 구합니다.
        now = int(time())
        window = now - now % self.WINDOW_SECONDS

        # 경로와 주소의 해시 및 구간 시작 시각으로 집계 행을 찾습니다.
        # 새 행을 만들 때는 현재 구간보다 오래된 집계 행을 정리합니다.
        bucket, created = LoginAttemptWindow.objects.get_or_create(key=key, window_start=window)
        if created:
            LoginAttemptWindow.objects.filter(window_start__lt=window).delete()

        # DB에서 한 번에 비교하고 증가시켜 서로 다른 프로세스에도 같은 제한을 적용합니다.
        allowed = LoginAttemptWindow.objects.filter(pk=bucket.pk, attempts__lt=limit).update(
            attempts=F("attempts") + 1
        )
        # update() 반환값은 변경된 행의 수입니다. 한 행이 증가하면 로그인 뷰로 진행하고,
        # 변경된 행이 없으면 429와 다음 구간까지 남은 초를 응답합니다.
        if allowed:
            return None

        return HttpResponse(
            "로그인 요청이 너무 많습니다. 잠시 뒤 다시 시도해 주세요.",
            status=429,
            content_type="text/plain; charset=utf-8",
            headers={"Retry-After": str(window + self.WINDOW_SECONDS - now), "Cache-Control": "no-store"},
        )
