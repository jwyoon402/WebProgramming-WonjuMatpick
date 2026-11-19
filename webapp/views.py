from random import choice

from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import RestaurantSearchForm
from .models import Menu, Restaurant


def home(request):
    return render(request, "webapp/home.html", {"categories": Restaurant.Category.choices})


@require_GET
def restaurant_list(request):
    form = RestaurantSearchForm(request.GET)
    restaurants = Restaurant.objects.none()
    if form.is_valid():
        keyword = form.cleaned_data["keyword"]
        category = form.cleaned_data["category"]
        district = form.cleaned_data["district"]
        max_price = form.cleaned_data["max_price"]
        restaurants = Restaurant.objects.all()
        if category:
            restaurants = restaurants.filter(category=category)
        if district:
            restaurants = restaurants.filter(
                Q(district__icontains=district) | Q(address__icontains=district)
            )

        # ������������ �޴����� ������ ���� �޴� �࿡ �����մϴ�.
        # Exists�� �Ǹ� �޴��� ���� ������ ������ ���� �� ���� ��ȯ�մϴ�.
        eligible_menus = Menu.objects.filter(restaurant_id=OuterRef("pk"))
        if max_price is not None:
            eligible_menus = eligible_menus.filter(price__lte=max_price)
        if keyword:
            name_match = Q(name__icontains=keyword)
            if max_price is not None:
                name_match &= Q(Exists(eligible_menus))
            menu_match = Exists(eligible_menus.filter(name__icontains=keyword))
            restaurants = restaurants.filter(name_match | Q(menu_match))
        elif max_price is not None:
            restaurants = restaurants.filter(Exists(eligible_menus))

    page = Paginator(restaurants, 12).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(request, "webapp/restaurant_list.html", {
        "form": form, "restaurants": page.object_list, "page": page,
        "query_string": query_params.urlencode(),
    })


@require_GET
def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    return render(request, "webapp/restaurant_detail.html", {
        "restaurant": restaurant, "menus": restaurant.menus.all(),
    })


@require_http_methods(["GET", "HEAD", "POST"])
def roulette(request):
    context = {"categories": Restaurant.Category.choices}
    if request.method == "POST":
        # (ī�װ���, �޴���) �ߺ��� ������ ���� �̸��� �޴��� �Ĵ� ���԰�
        # ���Ƶ� �� �޴� �Ǵ� ī�װ����� ��÷���� ���������� �ʵ��� �մϴ�.
        candidates = (
            Menu.objects.order_by()
            .values_list("restaurant__category", "name")
            .distinct()
        )
        menus_by_category = {}
        for category, menu_name in candidates:
            menus_by_category.setdefault(category, []).append(menu_name)

        if menus_by_category:
            selected_category = choice(list(menus_by_category))
            selected_menu = choice(menus_by_category[selected_category])
            # ��÷�� �޴��� �Ǹ�ó�� ����� ���, �� �Ǹ�ó�� ������ ����մϴ�.
            sellers = list(Menu.objects.select_related("restaurant").filter(
                name=selected_menu, restaurant__category=selected_category
            ).order_by("restaurant__name", "restaurant_id"))
            if sellers:
                context.update({
                    "selected_category": Restaurant.Category(selected_category).label,
                    "selected_menu": selected_menu,
                    "menu_image_url": next((menu.image_url for menu in sellers if menu.image_url), ""),
                    "sellers": sellers,
                })
        context["drawn"] = True
    return render(request, "webapp/roulette.html", context)
