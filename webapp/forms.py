from django import forms

from .models import Menu, Restaurant


class RestaurantSearchForm(forms.Form):
    keyword = forms.CharField(
        label="검색어", max_length=120, required=False,
        widget=forms.TextInput(attrs={"placeholder": "음식점 또는 메뉴 이름"}),
    )
    category = forms.ChoiceField(
        label="카테고리", choices=[("", "전체")] + Restaurant.Category.choices, required=False
    )
    district = forms.CharField(
        label="지역", max_length=60, required=False,
        widget=forms.TextInput(attrs={"placeholder": "예: 흥업면"}),
    )
    max_price = forms.IntegerField(
        label="최대 메뉴 가격(원)", min_value=1, max_value=Menu.MAX_PRICE, required=False,
        widget=forms.NumberInput(attrs={"placeholder": "예: 12000"}),
    )
