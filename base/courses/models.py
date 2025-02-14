from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название категории"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание категории"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время создания"
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Начинающий'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name="Название курса"
    )
    description = models.TextField(
        verbose_name="Описание курса"
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Преподаватель"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Стоимость курса"
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name="Уровень подготовки"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата последнего обновления"
    )
    category = models.ForeignKey(
        'Category',  # Связь с моделью Category
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses',
        verbose_name="Категория курса"
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликован?"
    )
    image = models.ImageField(
        upload_to='course_images/',  # Путь для сохранения изображений
        blank=True,
        null=True,
        verbose_name="Изображение курса"
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="Курс"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название урока"
    )
    content = models.TextField(
        verbose_name="Содержание урока"
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на видео"
    )
    order = models.PositiveIntegerField(
        verbose_name="Порядковый номер урока"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        ordering = ['order']
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"

    def __str__(self):
        return self.title


class Test(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='tests',
        verbose_name="Урок"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название теста"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание теста"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Тест"
    )
    text = models.TextField(
        verbose_name="Текст вопроса"
    )
    type = models.CharField(
        max_length=20,
        choices=[
            ('multiple_choice', 'Множественный выбор'),
            ('open_answer', 'Открытый ответ')
        ],
        verbose_name="Тип вопроса"
    )

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Вопрос"
    )
    text = models.CharField(
        max_length=255,
        verbose_name="Текст ответа"
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Правильный ответ?"
    )

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return self.text
