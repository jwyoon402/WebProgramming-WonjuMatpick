from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Review


def delete_unused_photo(storage, name, using):
    # DB 작업이 성공한 뒤에만 파일을 지웁니다. 다른 리뷰가 같은 파일을 쓰면 보존합니다.
    # 커밋 이후 동일한 DB에서 사진 경로를 다시 검색해, 경로를 참조하는 행이 없을 때만 삭제합니다.
    def cleanup():
        if not Review.objects.using(using).filter(photo=name).exists():
            storage.delete(name)

    if name:
        transaction.on_commit(cleanup, using=using, robust=True)


# 수정 전 DB에 있던 경로를 보관해 저장 후 현재 경로와 비교할 수 있게 합니다.
@receiver(pre_save, sender=Review)
def remember_previous_photo(sender, instance, raw, using, update_fields, **kwargs):
    instance.previous_photo_name = None
    # 초기 데이터 적재, 새 리뷰, 사진 필드를 건드리지 않는 부분 저장은 이전 경로를 조회할 필요가 없습니다.
    if raw or not instance.pk or (update_fields is not None and "photo" not in update_fields):
        return
    instance.previous_photo_name = (
        sender.objects.using(using).filter(pk=instance.pk).values_list("photo", flat=True).first()
    )


# 사진을 교체하거나 제거한 경우에만 이전 파일의 정리를 예약합니다.
@receiver(post_save, sender=Review)
def remove_replaced_photo(sender, instance, raw, using, **kwargs):
    previous = instance.previous_photo_name
    if not raw and previous and previous != instance.photo.name:
        delete_unused_photo(instance.photo.storage, previous, using)


# 리뷰 행이 삭제되면 삭제된 객체에 남은 사진 경로로 정리를 예약합니다.
@receiver(post_delete, sender=Review)
def remove_deleted_review_photo(sender, instance, using, **kwargs):
    # 사이트, 관리자, 음식점 연쇄 삭제에서 같은 정리 과정을 사용합니다.
    if instance.photo:
        delete_unused_photo(instance.photo.storage, instance.photo.name, using)
