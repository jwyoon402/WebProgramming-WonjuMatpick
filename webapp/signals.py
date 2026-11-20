from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Review


def delete_unused_photo(storage, name, using):
    # DB 작업이 성공한 뒤에만 파일을 지웁니다. 다른 리뷰가 같은 파일을 쓰면 보존합니다.
    def cleanup():
        if not Review.objects.using(using).filter(photo=name).exists():
            storage.delete(name)

    if name:
        transaction.on_commit(cleanup, using=using, robust=True)


@receiver(pre_save, sender=Review)
def remember_previous_photo(sender, instance, raw, using, update_fields, **kwargs):
    instance.previous_photo_name = None
    if raw or not instance.pk or (update_fields is not None and "photo" not in update_fields):
        return
    instance.previous_photo_name = (
        sender.objects.using(using).filter(pk=instance.pk).values_list("photo", flat=True).first()
    )


@receiver(post_save, sender=Review)
def remove_replaced_photo(sender, instance, raw, using, **kwargs):
    previous = instance.previous_photo_name
    if not raw and previous and previous != instance.photo.name:
        delete_unused_photo(instance.photo.storage, previous, using)


@receiver(post_delete, sender=Review)
def remove_deleted_review_photo(sender, instance, using, **kwargs):
    # 사이트, 관리자, 음식점 연쇄 삭제에서 같은 정리 과정을 사용합니다.
    if instance.photo:
        delete_unused_photo(instance.photo.storage, instance.photo.name, using)
