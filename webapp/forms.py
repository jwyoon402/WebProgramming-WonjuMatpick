from django import forms

from .models import Menu, Restaurant


class RestaurantSearchForm(forms.Form):
    keyword = forms.CharField(
        label="�˻���", max_length=120, required=False,
        widget=forms.TextInput(attrs={"placeholder": "������ �Ǵ� �޴� �̸�"}),
    )
    category = forms.ChoiceField(
        label="ī�װ���", choices=[("", "��ü")] + Restaurant.Category.choices, required=False
    )
    district = forms.CharField(
        label="����", max_length=60, required=False,
        widget=forms.TextInput(attrs={"placeholder": "��: �����"}),
    )
    max_price = forms.IntegerField(
        label="�ִ� �޴� ����(��)", min_value=1, max_value=Menu.MAX_PRICE, required=False,
        widget=forms.NumberInput(attrs={"placeholder": "��: 12000"}),
    )
