from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Create your models here.


class HeroBlock(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    subtitle = models.TextField(verbose_name="Описание")
    btn_to_action = models.CharField(
        max_length=255, verbose_name="Призыв к действию")
    hero_image = models.ImageField(
        upload_to='main_page/', blank=True, verbose_name="Главное изображение")

    class Meta:
        verbose_name = "Hero - секция"
        verbose_name_plural = "Hero - секция"

    def __str__(self):
        return self.title


class JoinOurCommunity(models.Model):
    title_block = models.CharField(
        max_length=255, verbose_name="Заголовок блока")
    subtitle_block = models.TextField(verbose_name="Описание блока")

    class Meta:
        verbose_name = "Название блока подписки"
        verbose_name_plural = "Описание блока подписки"

    def __str__(self):
        return self.title_block

# Приемущества подписки


class SubscriptionBenefit(models.Model):
    title_benefit = models.CharField(
        max_length=255, verbose_name="Заголовок преимущества")
    description_benefit = models.CharField(
        max_length=255, verbose_name="Описание преимущества")
    benefit_svg = models.FileField(
        upload_to='main_page/svg/',
        blank=True,
        verbose_name="SVG файл преимущества",
        help_text="Загрузите SVG файл. Только формат .svg разрешен."
    )

    class Meta:
        verbose_name = "Блок подписки"
        verbose_name_plural = "Блоки подписки"

    def __str__(self):
        return self.title_benefit

    def clean(self):
        """
        Валидация: Разрешаем загрузку только SVG файлов.
        """
        if self.benefit_svg and not self.benefit_svg.name.endswith('.svg'):
            raise ValidationError("Можно загружать только SVG файлы.")


class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"

    def __str__(self):
        return self.question


class Subscriber(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email подписчика")
    category = models.ForeignKey(
        'courses.Category',  
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Предпочитаемая категория"
    )
    subscribed_at = models.DateTimeField(
        default=timezone.now, verbose_name="Дата подписки")
    is_active = models.BooleanField(
        default=True, verbose_name="Активная подписка")
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="IP адрес")
    is_confirmed = models.BooleanField(
        default=False, verbose_name="Подтверждена")
    confirmation_token = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Токен подтверждения")

    class Meta:
        verbose_name = "Подписчик"
        verbose_name_plural = "Подписчики"
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email
