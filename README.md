# WebProgramming-WonjuMatpick

> **원주맛픽** — 원주시 맛집 탐색과 음식 추천 룰렛을 결합한 반응형 웹서비스
>
> **개발 상태:** 음식점·메뉴 관리, 검색, 상세, 추천 룰렛, 닉네임을 포함한 가입, 사진 리뷰, 관심 맛집, 팔로우 관리가 연결되어 있습니다.

## 프로젝트 소개

원주시의 음식점을 카테고리(한식·중식·일식·양식 등)와 검색어로 찾아보고, 음식점의 메뉴·사진·평점·리뷰를 확인하는 웹서비스입니다. 무엇을 먹을지 고민하는 사용자를 위해 무작위 음식 카테고리 추천 룰렛을 제공합니다.

## 기술 스택

| 구분 | 기술 |
| --- | --- |
| 프론트엔드 | HTML5, CSS3, Flexbox, 미디어 쿼리 |
| 백엔드 | Python, Django (View / Template) |
| DB | SQLite, Django ORM |
| 협업·기획 | GitHub, Figma |

JavaScript는 선택적으로 사용하며, 수업에서 배운 HTML/CSS와 Django를 중심으로 구현합니다.

## 주요 기능

- **맛집 탐색:** 음식점 이름/메뉴 검색, 음식 종류별 분류, 목록 및 상세정보 조회
- **회원:** 회원가입, 로그인, 마이페이지
- **리뷰:** 별점과 후기 등록·조회·수정·삭제, 선택 사진 첨부 및 교체·삭제 시 파일 정리
- **룰렛:** 무작위 음식 카테고리 추천 및 해당 카테고리 음식점 연결
- **사용자 교류:** 리뷰 작성자 프로필과 팔로우, 팔로잉 검색·언팔로우, 프로필에서 음식점 리뷰 이동
- **관리자:** 음식점 데이터 등록·조회·수정·삭제(CRUD)

**2차 과제 필수 요건:** 반응형 웹 프론트엔드, Django 백엔드, Django ORM 데이터 처리, 실제 작동하는 CRUD.

## 권장 프로젝트 구조

아래는 **권장안**이며, 백엔드 담당자가 Django 프로젝트를 생성한 후 실제 구조에 맞게 수정합니다.

```text
WebProgramming-WonjuMatpick/
├── config/                     # settings.py, urls.py 등
│   └── templates/
│       └── webapp/             # Django HTML 템플릿 (수업 실습 구조 참고)
├── webapp/                     # models.py, views.py, forms.py, admin.py, urls.py
│   └── migrations/             # 마이그레이션 파일은 Git에 포함
├── static/
│   ├── css/                    # Flexbox 및 반응형 스타일
│   └── images/                 # 저작권 문제 없는 정적 이미지
├── docs/
│   └── team_rules.md           # 협업 및 통합 규칙
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

**현재 적용:** 템플릿은 `config/templates/webapp/`, 정적 파일은 `static/`를 사용하도록 `config/settings.py`를 설정했습니다. 후속 변경은 팀원들과 협의합니다.

## 역할 분담

| 담당 | 주요 업무 |
| --- | --- |
| 프론트엔드 1 | 메인, 음식점 목록·검색·상세, 관리자 화면 UI |
| 프론트엔드 2 | 회원, 리뷰, 룰렛, 마이페이지·팔로잉 UI |
| 백엔드 1 | Restaurant/Menu 모델, 검색·룰렛, 관리자 CRUD |
| 백엔드 2 | 회원 및 리뷰 기능 : 회원가입, 로그인, 리뷰CRUD, 팔로우 기능 |
| 5번째 조원 (통합·테스트) | GitHub 구조·문서 관리, 공통 설정 조율, 반응형 및 기능 테스트, 제출물 확인 |

세부 작업 분담과 Pull Request 절차는 [팀 협업 규칙](docs/team_rules.md)을 참고하세요.

## 회원·리뷰·팔로우

- 홈에서 오늘의 맛집을 확인하고, 로그인 후 음식점 상세에서 관심 맛집을 등록할 수 있습니다.
- 회원가입에서 아이디와 닉네임을 입력하고 로그인합니다. 로그인 전 열려던 페이지가 있으면 해당 주소로 돌아갑니다.
- 음식점 상세에서 평균 별점과 리뷰를 확인하고, 로그인 후 리뷰를 작성할 수 있습니다.
- 리뷰 목록과 프로필에서 팔로우를 변경할 수 있고, 팔로잉 목록에서는 닉네임을 검색하거나 직접 팔로우를 해제할 수 있습니다.
- 리뷰 사진은 Pillow로 검증합니다. 사진 교체나 리뷰 삭제가 DB에 반영된 뒤, 참조되지 않는 이전 사진을 정리합니다.
- 기존 DB는 먼저 백업하고 `python manage.py migrate`로 닉네임 프로필 테이블을 추가합니다. 닉네임 프로필이 없는 기존 계정은 아이디를 표시합니다.

## 실행 방법

아래 명령을 `manage.py`가 있는 폴더에서 실행합니다. 기존 가상환경이 상위 폴더에 있으면 `..\.venv\Scripts\python.exe`를 사용합니다.

**Windows 명령 프롬프트(cmd)**

```cmd
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

브라우저에서 <http://127.0.0.1:8000/>을 엽니다. macOS/Linux에서는 `.venv/bin/python`을 사용합니다. 관리자 시연이 필요하면 별도 터미널에서 `.\.venv\Scripts\python.exe manage.py createsuperuser`로 관리자 계정을 만듭니다.

`seed_demo`는 시연용 DB에 가상 음식점 8곳, 메뉴 15개, 예시 리뷰 8개 및 로컬 시연 삽화를 준비합니다. 기존 계정 데이터를 사용하지 않고 팔로우를 시연하려면 사이트에서 자신의 시연 계정을 가입한 뒤 예시 리뷰 작성자를 팔로우하면 됩니다. 처음 시연 데이터를 넣을 때 주소나 포트를 바꾼다면 `seed_demo --base-url http://127.0.0.1:8001`과 `runserver 127.0.0.1:8001`처럼 같은 주소를 지정합니다.

## 음식점 기능 시연

| 주소 | 동작 |
| --- | --- |
| `/` | 카테고리 선택, 검색과 룰렛 진입 |
| `/restaurants/` | `keyword`, `category`, `district`, `max_price`, `min_rating`로 검색 및 필터 |
| `/restaurants/<id>/` | 음식점 정보와 메뉴 목록 조회 |
| `/roulette/` | GET으로 룰렛 표시, POST로 추첨한 뒤 결과로 이동 |
| `/roulette/result/` | 세션에 저장한 추첨 결과와 현재 판매점 목록 표시 |
| `/admin/` | 관리자 로그인 후 음식점과 메뉴 등록·조회·수정·삭제 |

1. 목록에서 검색어 `돈가스`, 최대 가격 `12000`을 입력합니다. 단계 돈가스집이 검색됩니다. 흥업 라멘집의 돈가스는 15,000원이므로 7,000원짜리 우동이 있어도 검색 결과에서 제외됩니다.
2. 룰렛을 돌려 추천 메뉴와 판매처를 확인합니다. 음식점을 클릭하면 상세 화면으로 이동합니다.
3. 음식점 상세의 리뷰 탭에서 전체 리뷰를 엽니다. 로그인 후 작성자를 팔로우하고, 내 프로필의 팔로잉 목록에서 닉네임으로 찾아 해제합니다.
4. 관리자에서 음식점과 메뉴를 등록하고 검색합니다. 메뉴 가격을 바꾸면 가격 검색 결과가 달라지며, 음식점을 삭제하면 연결된 메뉴도 함께 삭제됩니다.

`manage.py test`로 검색 조건, 상세 조회, 룰렛 후보와 판매처, CSRF, 관리자 권한 및 CRUD의 DB 반영을 확인할 수 있습니다.

## 팀 화면 연결

- URL 이름은 `webapp:restaurant_list`, `webapp:restaurant_detail`, `webapp:roulette`입니다. 음식점 상세 URL에는 `pk`를 전달합니다.
- 목록 템플릿은 `form`, `restaurants`, `page`를 전달받습니다. 상세 템플릿은 `restaurant`, `menus`를 사용합니다. 룰렛 결과는 `selected_category`, `selected_menu`, `sellers`를 사용하며, `sellers`의 각 항목은 판매 음식점과 가격을 가진 `Menu` 객체입니다.
- 음식점·메뉴 사진은 현재 선택 입력인 이미지 URL로 표시합니다. 관리자 CRUD는 Django 기본 관리자를 사용합니다.
- 음식점 상세는 평균 별점과 최신 리뷰를 보여 줍니다. 검색 목록에서도 최소 평점으로 필터링할 수 있습니다. 룰렛 회전 후 서버에서 선택한 메뉴와 판매처를 표시합니다.

## GitHub 및 보안

- 보안 보완본에서 `python -m pip install -r requirements.txt`로 Django 5.2.19 이상과 Pillow 13.0.0 이상을 설치하고 `python manage.py migrate`로 로그인 제한 테이블을 적용합니다.
- 일반 로그인과 관리자 로그인은 접속 주소별로 별도 제한합니다. 공용 프록시 뒤에서 여러 이용자의 주소가 같게 보이면 프록시에서도 이용자별 요청 제한을 설정합니다.
- 리뷰 사진은 JPEG·PNG·WebP 한 장을 받습니다. 5 MiB, 1,200만 픽셀, 한 변 6,000px이 상한이며, 서버에서 새 이미지로 저장해 원본 메타데이터를 제거합니다.
- 공개 환경은 `DJANGO_DEBUG=false`, 별도 랜덤 `DJANGO_SECRET_KEY`, 실제 `DJANGO_ALLOWED_HOSTS`를 설정합니다. HTTPS를 프록시에서 종료하는 경우, 프록시가 외부의 관련 헤더를 제거하고 자체 설정한다는 전제하에 `DJANGO_TRUST_PROXY_HTTPS=1`을 적용합니다. `DJANGO_MEDIA_URL`에는 업로드 파일을 제공하는 사이트의 HTTPS 주소를 지정하고, 프록시나 웹서버에서도 업로드 요청 크기를 제한합니다.
- `main`에는 가급적 직접 커밋하지 않고, 기능별 브랜치에서 PR을 생성합니다.
- `.venv/`, `db.sqlite3`, `.env`, `media/` 등 로컬·민감 파일은 업로드하지 않습니다.
- Django 마이그레이션 Python 파일은 협업을 위해 버전 관리합니다.
- 수업에서 제공된 교수님 강의자료 및 실습 원본 ZIP은 공개 저장소에 올리지 않습니다.
- 코드와 샘플 데이터는 본 프로젝트 구현 목적에 맞게 작성합니다.

## 제출 정보

2차 과제 마감: **2026년 11월 24일 23:59**. 제출 ZIP에 발표 PPT, 전체 소스코드, 실행방법 PDF를 포함합니다.
