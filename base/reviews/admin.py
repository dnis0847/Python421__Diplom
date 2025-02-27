from django.contrib import admin
from .models import Review  # Убедитесь, что путь к модели правильный

class ReviewAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке записей
    list_display = ('user', 'course', 'rating', 'created_at', 'comment_shortened')
    
    # Фильтры справа для быстрого поиска по определённым полям
    list_filter = ('rating', 'created_at', 'user', 'course')
    
    # Поиск по указанным полям
    search_fields = ('user__username', 'course__title', 'comment')
    
    # Сортировка по умолчанию
    ordering = ('-created_at',)
    
    # Добавление пагинации (если записей много)
    list_per_page = 20

    # Метод для отображения сокращенного комментария
    def comment_shortened(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_shortened.short_description = 'Комментарий'  # Название столбца

# Регистрация модели и её администратора
admin.site.register(Review, ReviewAdmin)