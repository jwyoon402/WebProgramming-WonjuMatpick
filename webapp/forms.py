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
    # 가격은 원 단위 정수, 평점은 소수 첫째 자리까지 받습니다. 비운 항목은 검색 조건에서 생략됩니다.
    max_price = forms.IntegerField(
        label="최대 메뉴 가격(원)", min_value=1, max_value=Menu.MAX_PRICE, required=False,
        widget=forms.NumberInput(attrs={"placeholder": "예: 12000"}),
    )


    min_rating = forms.DecimalField(
        label="최소 평점", min_value=1, max_value=5, max_digits=2, decimal_places=1,
        required=False, widget=forms.NumberInput(attrs={"step": "0.1", "placeholder": "예: 4.0"}),
    )


# [회원가입] Django UserCreationForm의 비밀번호 검증을 재사용하고 공개 닉네임을 별도로 저장합니다.
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
        # Django의 사용자 생성 폼이 비밀번호를 해시합니다. DB에 저장할 때 프로필도 함께 만들며,
        # 프로필 저장이 실패하면 같은 트랜잭션의 사용자 저장도 롤백됩니다.
        user = super().save(commit=commit)
        if commit:
            MemberProfile.objects.create(user=user, nickname=self.cleaned_data["nickname"])
        return user

# [사진 검증] 업로드 크기 → 이미지 내용/해상도 → 안전한 형식으로 재인코딩 순서로 처리합니다.
# 원본 파일의 메타데이터를 그대로 신뢰하거나 저장하지 않습니다.
class ReviewPhotoField(forms.FileField):
    # 사용자가 올린 파일과 변환 후 파일은 각각 최대 5 MiB까지 허용합니다.
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
                # 가로나 세로가 6,000픽셀을 넘거나 전체가 1,200만 픽셀을 넘으면 거절합니다.
                width, height = image.size
                if max(width, height) > self.MAX_EDGE or width * height > self.MAX_PIXELS:
                    raise forms.ValidationError("사진의 해상도가 너무 큽니다.", code="photo_dimensions")
                if getattr(image, "is_animated", False):
                    raise forms.ValidationError("정지 사진 한 장을 선택해 주세요.", code="photo_animation")
                mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
                # 회전 정보를 픽셀에 먼저 적용해 원본 메타데이터를 제거한 뒤에도 방향을 유지합니다.
                pixels = ImageOps.exif_transpose(image).convert(mode)
                # 픽셀만 새 이미지에 옮겨 원본 메타데이터 및 파일명을 저장하지 않습니다.
                clean = Image.new(mode, pixels.size)
                clean.paste(pixels)
                # 투명한 부분을 유지해야 하면 PNG로, 그 외에는 JPEG로 저장합니다.
                extension, output_format = ("png", "PNG") if mode == "RGBA" else ("jpeg", "JPEG")
                output = BytesIO()
                clean.save(output, format=output_format)
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
            raise forms.ValidationError("유효한 JPEG, PNG 또는 WebP 사진을 선택해 주세요.", code="photo_invalid") from exc

        if output.tell() > self.MAX_BYTES:
            raise forms.ValidationError("저장할 사진 용량은 5 MiB 이하여야 합니다.", code="photo_size")
        # 무작위 파일명과 다시 인코딩한 데이터로 업로드 객체를 만들어 리뷰 모델에 전달합니다.
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
        # 입력 가능한 필드를 제한합니다. 작성자와 음식점은 리뷰 생성 뷰에서 결정합니다.
        fields = ("rating", "content", "photo")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5, "maxlength": 2000}),
        }
        labels = {"rating": "별점 (1~5)", "content": "리뷰", "photo": "사진 (선택)"}


# 관리자 리뷰 편집에도 일반 리뷰 화면과 같은 사진 검증 및 변환을 적용합니다.
class AdminReviewForm(forms.ModelForm):
    photo = ReviewPhotoField()

    class Meta:
        model = Review
        fields = "__all__"
