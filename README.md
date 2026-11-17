# WebProgramming-WonjuMatpick

> **원주맛픽** — 원주시 맛집 탐색과 음식 추천 룰렛을 결합한 반응형 웹서비스
>
> **개발 상태:** 2차 웹프로그래밍 과제 진행 중. 아래 기능은 **기획 및 구현 목표**이며 완료를 의미하지 않습니다.

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

## 주요 기능 (기획)

- **맛집 탐색:** 음식점 이름/메뉴 검색, 음식 종류별 분류, 목록 및 상세정보 조회
- **회원:** 회원가입, 로그인, 마이페이지
- **리뷰:** 별점과 후기 등록·조회·수정·삭제, 사진 첨부(선택 구현)
- **룰렛:** 무작위 음식 카테고리 추천 및 해당 카테고리 음식점 연결
- **사용자 교류:** 사용자 프로필, 팔로우/언팔로우 및 팔로잉 목록(확장 기능)
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

**주의:** 템플릿 및 정적 파일의 실제 위치와 Django `settings.py` 설정을 반드시 일치시켜야 합니다. 기존에 작성된 팀원 코드를 확인한 뒤 구조를 확정합니다.

## 역할 분담

| 담당 | 주요 업무 |
| --- | --- |
| 프론트엔드 1 | 메인, 음식점 목록·검색·상세, 관리자 화면 UI |
| 프론트엔드 2 | 회원, 리뷰, 룰렛, 마이페이지·팔로잉 UI |
| 백엔드 1 | Restaurant/Menu 모델, 검색·룰렛, 관리자 CRUD |
| 백엔드 2 | 인증, Review/Follow 모델, 리뷰 CRUD, 사용자 기능 |
| 5번째 조원 (통합·테스트) | GitHub 구조·문서 관리, 공통 설정 조율, 반응형 및 기능 테스트, 제출물 확인 |

세부 작업 분담과 Pull Request 절차는 [팀 협업 규칙](docs/team_rules.md)을 참고하세요.

## 실행 방법 (소스코드 반영 후)

아래 명령은 **`manage.py`와 `requirements.txt`가 추가된 후** 저장소 루트에서 실행할 예정입니다. 지금 단계에서는 실행 가능한 Django 프로젝트가 아직 업로드되지 않았습니다.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

macOS/Linux에서는 `.venv/bin/python` 경로를 사용합니다. 기본 개발 서버 주소는 <http://127.0.0.1:8000/>입니다. 실제 경로·환경 변수·샘플 데이터 적재 방법은 개발 완료 후 갱신합니다.

## GitHub 및 보안

- `main`에는 가급적 직접 커밋하지 않고, 기능별 브랜치에서 PR을 생성합니다.
- `.venv/`, `db.sqlite3`, `.env`, `media/` 등 로컬·민감 파일은 업로드하지 않습니다.
- Django 마이그레이션 Python 파일은 협업을 위해 버전 관리합니다.
- 수업에서 제공된 교수님 강의자료 및 실습 원본 ZIP은 공개 저장소에 올리지 않습니다.
- 코드와 샘플 데이터는 본 프로젝트 구현 목적에 맞게 작성합니다.

## 제출 정보

2차 과제 마감: **2026년 11월 24일 23:59**. 제출 ZIP에 발표 PPT, 전체 소스코드, 실행방법 PDF를 포함합니다.
