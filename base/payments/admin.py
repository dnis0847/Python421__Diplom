from django.contrib import admin
from django.utils.html import format_html
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'course_link', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'course__title')

    def user_link(self, obj):
        return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
    user_link.short_description = 'Пользователь'

    def course_link(self, obj):
        return format_html('<a href="/admin/courses/course/{}/change/">{}</a>', obj.course.id, obj.course.title)
    course_link.short_description = 'Курс'