# 원주맛픽 팀 협업 규칙

> 5인 팀 협업을 위한 초안입니다. 실제 담당자·URL·폴더 구조는 팀원들과 합의한 뒤 조정합니다.

## 1. 브랜치 및 Pull Request

- `main`: 안정적으로 실행되는 통합 코드만 유지합니다. 원칙적으로 직접 커밋하지 않습니다.
- 프론트엔드: `feature/frontend-main`, `feature/frontend-user`
- 백엔드: `feature/backend-restaurant`, `feature/backend-user`
- 통합 담당: `chore/integration` (필요할 때)
- 작업 흐름: 최신 `main` 확인 → 담당 브랜치 작업 → PR 생성 → 다른 팀원 최소 1인 검토 → 병합 → 통합 테스트.
- 서로 같은 파일을 수정한다면 사전에 담당자와 편집 범위를 조율합니다.
- 브랜치명은 권장 예시이며 실제 생성 여부와는 별개입니다.

## 2. 담당 영역

| 역할 | 주요 범위 | 충돌 주의 |
| --- | --- | --- |
| 프론트엔드 1 | 홈, 맛집 검색·목록·상세, 관리자 UI와 CSS | 공통 `base.html`, 전역 CSS |
| 프론트엔드 2 | 인증, 리뷰, 룰렛, 마이페이지·프로필·팔로잉 UI | 공통 `base.html`, 전역 CSS |
| 백엔드 1 | 음식점·메뉴 모델, 검색, 룰렛, 관리자 CRUD | `models.py`, `urls.py`, `views.py` |
| 백엔드 2 | 계정 인증, 리뷰, 팔로우 관련 Model/Form/View | `models.py`, `urls.py`, `views.py` |
| 통합 담당 | 협업 문서, 통합 점검, 브라우저 폭별 테스트, 실행 안내 | `settings.py`, 공통 설정 |

`settings.py`, `urls.py`, `models.py` 등 공통 Django 파일은 한 팀원이 통합 편집하거나, PR마다 관련 팀원끼리 충돌을 확인합니다.

## 3. 프론트엔드 ↔ 백엔드 사전 합의

- HTML 템플릿 위치는 수업 실습을 참고한 `config/templates/webapp/`를 우선 제안합니다. Django `TEMPLATES` 설정에 맞춰 최종 확정합니다.
- 정적 파일은 `static/css/`, `static/images/`를 기본으로 제안하고 Django 설정과 일치시킵니다.
- URL은 이름을 부여해서 템플릿에서 `{% url 'webapp:...' %}` 형태로 참조합니다.
- 제안 URL: `/restaurants/`, `/restaurants/<id>/`, `/reviews/`, `/roulette/`, `/accounts/login/`. **확정 경로가 아닌 예시**입니다.
- 입력 필드 제안: 맛집 검색 `keyword`, `category`; 리뷰 `rating`, `content`, `photo`.
- 리뷰 사진을 구현하는 경우 폼에 `enctype="multipart/form-data"`를 사용하고, Django `request.FILES`로 받습니다.
- 각 화면에서 사용하는 컨텍스트 변수(예: `restaurants`, `restaurant`, `reviews`)도 프론트/백 담당자가 미리 합의합니다.

## 4. Django ORM / DB / 보안

- 모델 변경 후 `python manage.py makemigrations`와 `python manage.py migrate`를 실행합니다.
- `migrations/`의 마이그레이션 Python 파일은 Git에 올립니다. 충돌 시 삭제나 재생성을 임의로 하지 않고 담당자와 협의합니다.
- `.venv/`, `db.sqlite3`, `.env`, `media/` 등은 커밋하지 않습니다. Django `SECRET_KEY` 및 서비스 비밀정보는 공개 저장소에 게시하지 않습니다.
- 각자의 SQLite DB는 로컬에서 생성하고, 시연용 데이터는 fixture 또는 적재 스크립트로 별도 공유합니다.
- 리뷰 수정·삭제는 작성자 본인만, 관리자 음식점 CRUD는 관리자 권한을 가진 계정만 수행할 수 있도록 서버에서 검사합니다.
- 삭제 및 변경은 POST 같은 적절한 HTTP 메서드로 처리하고 `{% csrf_token %}`을 적용합니다. GET 링크만으로 데이터를 삭제하지 않습니다.
- 수업에서 받은 강의자료나 실습 원본 ZIP 파일은 공개 저장소에 업로드하지 않습니다.

## 5. PR 작성 원칙

- 제목 예: `[FE] 맛집 목록 반응형 UI`, `[BE] 리뷰 CRUD`, `[DOCS] 실행방법 정리`
- 본문에는 **변경 파일, 구현 기능, 테스트 방법/결과, 미완료 사항, UI 변경 스크린샷(해당 시)**을 작성합니다.
- 다른 팀원 최소 한 명이 변경 사항을 검토한 뒤 병합합니다.
- 병합 후 `main`에서 `python manage.py check` 등 가능한 검사와 핵심 페이지 실행을 확인합니다.

## 6. 통합·시연 체크리스트

- [ ] 다른 팀원이 README와 `requirements.txt`만으로 프로젝트를 설치하고 실행할 수 있다.
- [ ] Django View/Template와 ORM 데이터가 실제로 연결된다.
- [ ] 맛집 검색, 카테고리 필터, 상세페이지가 정상 동작한다.
- [ ] 회원가입 및 로그인, 리뷰 작성/조회/수정/삭제가 동작하며 권한 검사가 적용된다.
- [ ] 룰렛 결과가 선택된 음식 카테고리와 일치하고 연관 음식점을 확인할 수 있다.
- [ ] 음식점 관리자 CRUD가 실제 SQLite 데이터에 반영된다.
- [ ] 브라우저 너비 변화에 따라 Flexbox/미디어 쿼리 레이아웃이 정상 작동한다.
- [ ] 팔로우·사진 업로드 등 추가 구현 기능도 구현 시 별도 테스트한다.
- [ ] 제출 ZIP에 발표 PPT, 전체 소스코드, 실행방법 PDF를 포함한다.
