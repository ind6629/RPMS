import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import User


def _delete_avatar_file(path):
    if path and os.path.exists(path):
        os.remove(path)


@receiver(pre_save, sender=User)
def cleanup_replaced_avatar(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_user = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_avatar = getattr(old_user, 'avatar', None)
    new_avatar = getattr(instance, 'avatar', None)
    if not old_avatar:
        return
    if new_avatar and old_avatar.name == new_avatar.name:
        return

    _delete_avatar_file(old_avatar.path)


@receiver(post_delete, sender=User)
def cleanup_deleted_avatar(sender, instance, **kwargs):
    avatar = getattr(instance, 'avatar', None)
    if avatar:
        _delete_avatar_file(avatar.path)
