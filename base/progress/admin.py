from django.contrib import admin
from .models import Progress

# Register your models here.


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'score', 'started_at',
                    'completed_at', 'completed_lessons_count')
    list_filter = ('course', 'started_at', 'completed_at')
    search_fields = ('user__username', 'course__title')
    readonly_fields = ('started_at', 'completed_at')

    def completed_lessons_count(self, obj):
        return obj.completed_lessons.count()
    completed_lessons_count.short_description = 'Количество завершенных уроков'


admin.site.register(Progress, ProgressAdmin)
