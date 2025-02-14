from .models import Test
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from payments.models import Payment
from .models import (
    Category,
    Course,
    Lesson,
    Test,
    Question,
    Answer,
)

# Модель Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

# Модель Course
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('user', 'amount', 'status', 'created_at')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'teacher',
        'category',
        'price',
        'level',
        'is_published',
        'created_at'
    )
    list_filter = ('category', 'level', 'is_published',
                   'created_at')  # Фильтры
    search_fields = ('title', 'teacher__username', 'category__name')  # Поиск
    readonly_fields = ('created_at', 'updated_at')  # Только для чтения
    fieldsets = (
        ("Основная информация", {
            'fields': ('title', 'description', 'teacher', 'category', 'price', 'level', 'is_published')
        }),
        ("Изображение", {
            'fields': ('image',)
        }),
        ("Даты", {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [PaymentInline]

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "Нет изображения"
    display_image.short_description = "Изображение"

# Модель Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course', 'created_at')  # Фильтры
    search_fields = ('title', 'course__title')  # Поиск
    readonly_fields = ('created_at',)  # Только для чтения


# Модель Test
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'created_at')
    list_filter = ('lesson', 'created_at')  # Фильтры
    search_fields = ('title', 'lesson__title')  # Поиск
    readonly_fields = ('created_at',)  # Только для чтения


# Модель Question
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'type')
    list_filter = ('type', 'test')  # Фильтры
    search_fields = ('text', 'test__title')  # Поиск


# Модель Answer
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question')  # Фильтры
    search_fields = ('text', 'question__text')  # Поиск
    list_editable = ('is_correct',)  # Быстрое редактирование


