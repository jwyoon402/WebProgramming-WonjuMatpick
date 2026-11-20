from io import BytesIO
from uuid import uuid4

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from PIL import Image, ImageOps

from .models import MemberProfile, Menu, Restaurant, Review


# 검색어와 필터를 검증하고, 가격·평점은 ORM 조건에 쓸 수 있는 숫자 형식으로 변환합니다.
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


    min_rating = forms.DecimalField(
        label="최소 평점", min_value=1, max_value=5, max_digits=2, decimal_places=1,
        required=False, widget=forms.NumberInput(attrs={"step": "0.1", "placeholder": "예: 4.0"}),
    )


class SignupForm(UserCreationForm):
    email = forms.EmailField(label="이메일", required=True)
    nickname = forms.CharField(label="닉네임", max_length=30)

    class Meta:
        model = get_user_model()
        fields = ("username", "nickname", "email", "password1", "password2")

    # 이메일 앞뒤 공백과 대소문자를 정리하고, 기존 계정에 같은 이메일이 있는지 조회합니다.
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if self._meta.model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        # 사용자와 닉네임 프로필을 한 트랜잭션으로 등록합니다.
        user = super().save(commit=commit)
        if commit:
            MemberProfile.objects.create(user=user, nickname=self.cleaned_data["nickname"])
        return user

class ReviewPhotoField(forms.FileField):
    MAX_BYTES = 5 * 1024 * 1024
    MAX_PIXELS = 12_000_000
    MAX_EDGE = 6000
    FORMATS = ("JPEG", "PNG", "WEBP")

    def __init__(self):
        super().__init__(
            label="사진 (선택)", required=False,
            help_text="JPEG, PNG, WebP 한 장. 최대 5 MiB, 1,200만 픽셀.",
            widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        )

    def to_python(self, data):
        upload = super().to_python(data)
        if upload is None:
            return None
        if upload.size > self.MAX_BYTES:
            raise forms.ValidationError("사진 용량은 5 MiB 이하여야 합니다.", code="photo_size")

        try:
            # 파일명과 MIME 형식 대신 실제 내용으로 확인하고 픽셀을 읽기 전에 해상도를 제한합니다.
            with Image.open(upload, formats=self.FORMATS) as image:
                width, height = image.size
                if max(width, height) > self.MAX_EDGE or width * height > self.MAX_PIXELS:
                    raise forms.ValidationError("사진의 해상도가 너무 큽니다.", code="photo_dimensions")
                if getattr(image, "is_animated", False):
                    raise forms.ValidationError("정지 사진 한 장을 선택해 주세요.", code="photo_animation")
                mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
                pixels = ImageOps.exif_transpose(image).convert(mode)
                # 픽셀만 새 이미지에 옮겨 원본 메타데이터 및 파일명을 저장하지 않습니다.
                clean = Image.new(mode, pixels.size)
                clean.paste(pixels)
                extension, output_format = ("png", "PNG") if mode == "RGBA" else ("jpeg", "JPEG")
                output = BytesIO()
                clean.save(output, format=output_format)
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
            raise forms.ValidationError("유효한 JPEG, PNG 또는 WebP 사진을 선택해 주세요.", code="photo_invalid") from exc

        if output.tell() > self.MAX_BYTES:
            raise forms.ValidationError("저장할 사진 용량은 5 MiB 이하여야 합니다.", code="photo_size")
        return SimpleUploadedFile(f"{uuid4().hex}.{extension}", output.getvalue(), f"image/{extension}")


# 리뷰 생성과 수정에서 같은 폼을 사용합니다. 별점은 1~5 중 하나이고 사진은 선택 항목입니다.
class ReviewForm(forms.ModelForm):
    photo = ReviewPhotoField()
    rating = forms.TypedChoiceField(
        label="별점", choices=[(score, f"{'★' * score} {score}점") for score in range(1, 6)],
        coerce=int, widget=forms.RadioSelect,
    )

    class Meta:
        model = Review
        fields = ("rating", "content", "photo")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5, "maxlength": 2000}),
        }
        labels = {"rating": "별점 (1~5)", "content": "리뷰", "photo": "사진 (선택)"}


class AdminReviewForm(forms.ModelForm):
    photo = ReviewPhotoField()

    class Meta:
        model = Review
        fields = "__all__"
