# models.py
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="Пользователь")
    bio = models.TextField(blank=True, null=True,
                           verbose_name="Информация о профиле")
    avatar = models.ImageField(
        upload_to='avatars/', blank=True, null=True, verbose_name="Фото профиля")
    role = models.CharField(
        max_length=20,
        choices=[('admin', 'Админ'), ('teacher', 'Учитель'),
                 ('student', 'Студент')],
        default='student', verbose_name="Роль пользователя",
    )

    def __str__(self):
        return f"Профиль пользователя с ником: {self.user.username}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
