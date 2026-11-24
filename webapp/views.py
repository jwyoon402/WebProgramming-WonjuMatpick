from random import Random, choice
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import RestaurantSearchForm, ReviewForm, SignupForm
from .models import Favorite, Follow, Menu, Restaurant, Review

User = get_user_model()


def local_return_url(request):
    # 로그인과 팔로우 처리 후에는 현재 사이트의 주소로만 돌아갑니다.
    # 폼으로 제출된 복귀 주소를 우선하고, 없으면 URL의 next 값을 확인합니다.
    # 현재 호스트로 이동할 수 있는 주소만 허용하며, HTTPS 요청의 복귀에도 HTTPS를 요구합니다.
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return ""


def home(request):
    # 메뉴가 등록된 음식점만 추천 후보로 조회합니다.
    # distinct()로 메뉴가 여러 개인 음식점도 후보에 한 번만 들어갑니다.
    candidates = list(Restaurant.objects.filter(menus__isnull=False).order_by("pk").distinct())
    # 날짜를 난수 시드로 쓰고 후보를 PK 순으로 고정해, 후보가 같으면 그날의 추천도 같습니다.
    recommendation = Random(timezone.localdate().toordinal()).choice(candidates) if candidates else None
    return render(request, "webapp/home.html", {
        "categories": Restaurant.Category.choices, "recommendation": recommendation,
    })


@require_GET
    # [데이터 흐름] GET 검색값 → Form 검증 → ORM 필터 → 12개씩 페이지 분할 → 템플릿 전달.
def restaurant_list(request):
    form = RestaurantSearchForm(request.GET)
    restaurants = Restaurant.objects.none().order_by("name", "pk")
    # 쿼리스트링을 폼에서 검증한 뒤 통과한 값으로만 ORM 검색 조건을 만듭니다.
    # 검색 조건이 잘못되면 빈 결과와 폼 오류를 화면에 전달합니다.
    if form.is_valid():
        keyword = form.cleaned_data["keyword"]
        category = form.cleaned_data["category"]
        district = form.cleaned_data["district"]
        max_price = form.cleaned_data["max_price"]
        # 리뷰의 평균 별점을 음식점별로 계산해 검색 결과 표시와 최소 평점 필터에 사용합니다.
        restaurants = Restaurant.objects.annotate(average_rating=Avg("reviews__rating")).order_by("name", "pk")
        # 최소 평점을 지정하면 리뷰가 없어 평균이 NULL인 음식점은 결과에서 빠집니다.
        if form.cleaned_data["min_rating"] is not None:
            restaurants = restaurants.filter(average_rating__gte=form.cleaned_data["min_rating"])
        if category:
            restaurants = restaurants.filter(category=category)
        if district:
            restaurants = restaurants.filter(
                Q(district__icontains=district) | Q(address__icontains=district)
            )

        # 서브쿼리에서 메뉴명과 가격을 같은 메뉴 행에 적용합니다.
        # Exists는 판매 메뉴가 여러 개여도 음식점 행을 한 번만 반환합니다.
        eligible_menus = Menu.objects.filter(restaurant_id=OuterRef("pk"))
        if max_price is not None:
            eligible_menus = eligible_menus.filter(price__lte=max_price)
        # 가게 이름이 일치하면 가격 조건을 만족하는 메뉴가 하나 이상 있어야 합니다.
        # 메뉴 이름으로 찾을 때는 이름과 가격을 같은 행에서 확인합니다. 예를 들어
        # 15,000원 돈가스와 7,000원 우동만 파는 집은 메뉴명 기준 돈가스 12,000원 이하 검색에 나오지 않습니다.
        if keyword:
            name_match = Q(name__icontains=keyword)
            if max_price is not None:
                name_match &= Q(Exists(eligible_menus))
            menu_match = Exists(eligible_menus.filter(name__icontains=keyword))
            restaurants = restaurants.filter(name_match | Q(menu_match))
        elif max_price is not None:
            restaurants = restaurants.filter(Exists(eligible_menus))

    # 조회 결과를 12곳씩 나누고, 페이지 링크에 현재 검색 조건을 전달합니다.
    page = Paginator(restaurants, 12).get_page(request.GET.get("page"))
    # 기존 페이지 번호를 제외한 검색 조건을 복사해 다음 페이지 링크에 다시 붙입니다.
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(request, "webapp/restaurant_list.html", {
        "form": form, "restaurants": page.object_list, "page": page,
        "query_string": query_params.urlencode(),
    })


@require_GET
def restaurant_detail(request, pk):
    # URL의 PK로 음식점을 조회합니다. 없는 음식점은 404로 처리합니다.
    restaurant = get_object_or_404(Restaurant, pk=pk)
    # 작성자와 공개 닉네임을 리뷰와 함께 조회합니다. 전체 평균과 개수는 DB에서 집계하고,
    # 화면에는 모델의 최신순 정렬을 적용한 리뷰 중 처음 5건을 전달합니다.
    reviews = restaurant.reviews.select_related("author__member_profile")
    review_stats = reviews.aggregate(count=Count("pk"), average=Avg("rating"))
    return render(request, "webapp/restaurant_detail.html", {
        "restaurant": restaurant,
        "menus": restaurant.menus.all(),
        "reviews": reviews[:5],
        "review_count": review_stats["count"],
        "average_rating": review_stats["average"],
        "active_section": "reviews" if request.GET.get("section") == "reviews" else "menu",
        "is_favorite": request.user.is_authenticated and restaurant.favorites.filter(user=request.user).exists(),
    })


@login_required
@require_POST
def set_favorite(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    # 로그인한 사용자의 관심 목록만 변경합니다. 같은 음식점을 다시 추가해도 한 건만 저장합니다.
    # 대상 음식점과 세션의 사용자로 관계를 좁힌 뒤 버튼의 add/remove 값에 따라 저장하거나 삭제합니다.
    favorites = Favorite.objects.filter(user=request.user, restaurant=restaurant)
    if request.POST.get("action") == "add":
        Favorite.objects.get_or_create(user=request.user, restaurant=restaurant)
    elif request.POST.get("action") == "remove":
        favorites.delete()
    return redirect("webapp:restaurant_detail", pk=pk)


@login_required
@require_GET
def favorite_list(request):
    # 관심 목록과 연결된 음식점 중 현재 사용자에 해당하는 행만 조회합니다.
    restaurants = Restaurant.objects.filter(favorites__user=request.user)
    return render(request, "webapp/favorites.html", {"restaurants": restaurants})


@require_http_methods(["GET", "HEAD", "POST"])
    # [데이터 흐름] POST에서 DB 메뉴를 추첨하고 세션에 저장한 뒤 결과 GET으로 이동합니다.
def roulette(request):
    if request.method == "POST":
        # (카테고리, 메뉴명) 중복을 제거해 같은 이름의 메뉴를 파는 가게가
        # 많아도 그 메뉴 또는 카테고리가 추첨에서 유리해지지 않도록 합니다.
        candidates = (
            Menu.objects.order_by()
            .values_list("restaurant__category", "name")
            .distinct()
        )
        # 카테고리별로 메뉴명을 묶습니다. 등록된 메뉴가 없는 카테고리는 후보에 들어가지 않습니다.
        menus_by_category = {}
        for category, menu_name in candidates:
            menus_by_category.setdefault(category, []).append(menu_name)

        # 먼저 카테고리를 하나 뽑고, 그 안에 등록된 고유 메뉴명에서 하나를 뽑습니다.
        selection = []
        if menus_by_category:
            category = choice(list(menus_by_category))
            selection = [category, choice(menus_by_category[category])]
        # 새로고침 시 추첨을 반복하지 않도록 결과를 세션에 담아 GET 화면으로 보냅니다.
        request.session["roulette_selection"] = selection
        return redirect("webapp:roulette_result")
    return render(request, "webapp/roulette.html", {"categories": Restaurant.Category.choices})


@require_GET
def roulette_result(request):
    selection = request.session.get("roulette_selection")
    # 추첨 기록이 없는 직접 방문은 룰렛 화면으로 돌려보냅니다.
    # 빈 리스트는 추첨을 요청했으나 후보가 없었다는 뜻이므로 결과 화면에서 처리합니다.
    if selection is None:
        return redirect("webapp:roulette")
    categories = Restaurant.Category.choices
    context = {"categories": categories, "drawn": True}
    if selection:
        category, name = selection
        # 결과 페이지를 열 때 추첨된 메뉴의 현재 판매처와 가격을 다시 조회합니다.
        sellers = list(Menu.objects.select_related("restaurant").filter(
            name=name, restaurant__category=category
        ).order_by("restaurant__name", "restaurant_id"))
        if sellers:
            # 카테고리 하나가 60도를 차지합니다. 네 바퀴 각도에서 선택 칸 중앙의 각도를 빼 회전 목표를 정합니다.
            category_index = Restaurant.Category.values.index(category)
            context.update({
                "selected_category": Restaurant.Category(category).label,
                "selected_menu": name,
                "menu_image_url": next((menu.image_url for menu in sellers if menu.image_url), ""),
                "sellers": sellers,
                "wheel_angle": 1440 - (category_index * 60 + 30),
            })
    return render(request, "webapp/roulette.html", context)


def user_login(request):
    next_url = local_return_url(request)
    if request.user.is_authenticated:
        return redirect(next_url or "webapp:home")
    # Django 인증 폼이 아이디와 비밀번호를 검증하고, 성공하면 로그인 세션을 만듭니다.
    form = AuthenticationForm(request, data=request.POST if request.method == "POST" else None)
    # GET은 빈 로그인 폼을 표시합니다. POST 검증이 성공하면 확인된 사용자를 세션에 연결합니다.
    # 실패하면 입력 오류가 담긴 폼을 다시 표시합니다.
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "로그인되었습니다.")
        return redirect(next_url or "webapp:home")
    return render(request, "registration/login.html", {"form": form, "next": next_url})


@require_POST
def user_logout(request):
    # 로그아웃은 POST로 받아 로그인 세션을 지운 뒤 로그인 화면으로 이동합니다.
    auth_logout(request)
    messages.info(request, "로그아웃되었습니다.")
    return redirect("webapp:login")


def signup(request):
    if request.user.is_authenticated:
        return redirect("webapp:profile", user_id=request.user.pk)
    next_url = local_return_url(request)
    # 입력값 검증을 통과하면 계정을 저장하고 로그인 화면으로 이동합니다.
    form = SignupForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "회원가입이 완료되었습니다. 로그인해 주세요.")
        # 가입 후 로그인할 때도 원래 화면으로 돌아갈 수 있도록 검증된 복귀 주소를 넘깁니다.
        login_url = reverse("webapp:login")
        return redirect(f"{login_url}?{urlencode({'next': next_url})}" if next_url else login_url)
    return render(request, "webapp/signup.html", {"form": form, "next": next_url})

def profile(request, user_id):
    # 프로필 사용자와 작성 리뷰를 조회하고, 팔로우 관계의 양쪽 방향을 따로 집계합니다.
    profile_user = get_object_or_404(User.objects.select_related("member_profile"), pk=user_id)
    reviews = Review.objects.filter(author=profile_user).select_related("restaurant")
    # 이 사용자가 팔로우 대상인 행과 팔로우를 시작한 행을 각각 셉니다.
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    is_following = request.user.is_authenticated and request.user.pk != profile_user.pk and Follow.objects.filter(follower=request.user, following=profile_user).exists()
    return render(request, "webapp/profile.html", {
        "profile_user": profile_user, "reviews": reviews,
        "followers_count": followers_count, "following_count": following_count,
        "is_following": is_following,
    })

def review_list(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    # 해당 음식점에 연결된 리뷰만 조회하고, 화면에서 쓸 작성자와 음식점도 함께 가져옵니다.
    reviews = restaurant.reviews.select_related("author__member_profile")
    if request.user.is_authenticated:
        # 리뷰마다 작성자를 팔로우하는지 한 번의 ORM 조회에 함께 계산합니다.
        # 바깥 리뷰 행의 author_id를 참조해 현재 사용자와 작성자 사이의 관계가 있는지 확인합니다.
        follows_author = Follow.objects.filter(follower=request.user, following_id=OuterRef("author_id"))
        reviews = reviews.annotate(follows_author=Exists(follows_author))
    return render(request, "webapp/review_list.html", {
        "reviews": reviews, "restaurant_id": restaurant_id, "restaurant": restaurant,
    })

@login_required
    # [작성자 보호] 리뷰의 작성자는 세션, 식당은 URL의 PK로 결정하며 폼에서 받지 않습니다.
def review_create(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    # 리뷰 폼은 본문과 별점, 선택적으로 첨부된 사진을 함께 검증합니다.
    form = ReviewForm(request.POST, request.FILES) if request.method == "POST" else ReviewForm()
    if request.method == "POST" and form.is_valid():
        # 폼은 리뷰 내용만 받습니다. 음식점은 URL에서 조회한 객체, 작성자는 세션 사용자로 정합니다.
        # commit=False로 DB 저장을 미루고 이 두 값을 채운 뒤 새 리뷰 행을 저장합니다.
        review = form.save(commit=False)
        review.restaurant = restaurant
        review.author = request.user
        review.save()
        messages.success(request, "리뷰가 등록되었습니다.")
        return redirect("webapp:review_list", restaurant_id=restaurant_id)
    return render(request, "webapp/review_form.html", {"form": form, "restaurant_id": restaurant_id, "title": "리뷰 작성"})

@login_required
    # [수정 권한] DB의 리뷰 작성자와 현재 로그인 사용자 PK가 같은지 먼저 확인합니다.
def review_update(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    # 기존 데이터를 폼에 채우거나 변경 사항을 받기 전에 로그인 사용자와 원래 작성자의 PK를 비교합니다.
    if review.author_id != request.user.pk:
        messages.error(request, "본인이 작성한 리뷰만 수정할 수 있습니다.")
        return redirect("webapp:review_list", restaurant_id=review.restaurant_id)
    # 기존 리뷰를 폼에 전달해 작성자가 유효한 변경을 제출하면 같은 행을 갱신합니다.
    form = ReviewForm(request.POST, request.FILES, instance=review) if request.method == "POST" else ReviewForm(instance=review)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "리뷰가 수정되었습니다.")
        return redirect("webapp:review_list", restaurant_id=review.restaurant_id)
    return render(request, "webapp/review_form.html", {"form": form, "restaurant_id": review.restaurant_id, "title": "리뷰 수정"})

@login_required
@require_POST
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    restaurant_id = review.restaurant_id
    # POST 요청에서 작성자 소유권을 확인한 뒤 해당 리뷰 행을 삭제합니다.
    if review.author_id != request.user.pk:
        messages.error(request, "본인이 작성한 리뷰만 삭제할 수 있습니다.")
    else:
        # 리뷰 삭제 신호가 사진 경로를 확인하고 DB 커밋 이후 파일 정리를 예약합니다.
        review.delete()
        messages.success(request, "리뷰가 삭제되었습니다.")
    return redirect("webapp:review_list", restaurant_id=restaurant_id)

@login_required
@require_POST
def follow_toggle(request, user_id):
    target = get_object_or_404(User.objects.select_related("member_profile"), pk=user_id)
    next_url = local_return_url(request)
    if target.pk == request.user.pk:
        messages.error(request, "자기 자신은 팔로우할 수 없습니다.")
    else:
        relation = Follow.objects.filter(follower=request.user, following=target)
        # 명시적인 follow/unfollow 버튼은 같은 요청을 여러 번 보내도 같은 최종 상태를 유지합니다.
        action = request.POST.get("action")
        if action == "follow":
            relation.get_or_create(follower=request.user, following=target)
            messages.success(request, "팔로우했습니다.")
        elif action == "unfollow":
            relation.delete()
            messages.info(request, "팔로우를 취소했습니다.")
        elif action is None:
            # 이전 화면에서 보내던 동작 값 없는 요청도 처리합니다.
            with transaction.atomic():
                existing, created = relation.get_or_create(follower=request.user, following=target)
                if not created:
                    existing.delete()
    return redirect(next_url or reverse("webapp:profile", args=[target.pk]))

def follow_list(request, user_id, kind):
    profile_user = get_object_or_404(User.objects.select_related("member_profile"), pk=user_id)
    # 팔로워는 이 사용자를 팔로우하는 사람이고, 팔로잉은 이 사용자가 팔로우하는 사람입니다.
    if kind == "followers":
        related_ids = Follow.objects.filter(following=profile_user).values_list("follower_id", flat=True)
        title = "팔로워 목록"
    elif kind == "following":
        related_ids = Follow.objects.filter(follower=profile_user).values_list("following_id", flat=True)
        title = "팔로잉 목록"
    else:
        return redirect("webapp:profile", user_id=profile_user.pk)
    keyword = request.GET.get("q", "").strip()[:30]
    # 조회 방향에 맞춰 뽑은 사용자 ID로 목록을 구성하고, 닉네임 또는 아이디로 좁힙니다.
    people = User.objects.filter(pk__in=related_ids).select_related("member_profile")
    if keyword:
        people = people.filter(Q(member_profile__nickname__icontains=keyword) | Q(username__icontains=keyword))
    # 여러 관계를 함께 집계하므로 조인에서 생긴 중복 행을 제외합니다.
    people = people.annotate(
        followers_count=Count("follower_relations", distinct=True),
        following_count=Count("following_relations", distinct=True),
        review_count=Count("reviews", distinct=True),
    ).order_by("member_profile__nickname", "username")
    return render(request, "webapp/follow_list.html", {
        "profile_user": profile_user, "people": people, "title": title, "keyword": keyword,
        "can_unfollow": kind == "following" and request.user.pk == profile_user.pk,
    })
