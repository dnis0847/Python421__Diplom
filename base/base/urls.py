from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainPage.urls')),
    path('users/', include('users.urls')),
    path('courses/', include('courses.urls')),
    path('payments/', include('payments.urls')),
]

# Обслуживание медиафайлов и статических файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Обработчик страницы 404
handler404 = 'mainPage.views.custom_page_not_found'