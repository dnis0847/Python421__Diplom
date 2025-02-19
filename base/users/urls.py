from django.urls import path
from .views import RegisterView, UserLoginView, custom_logout, DashboardView, CourseDetailView, LessonDetailView, lesson_detail, mark_lesson_complete


app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('course/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('lesson/<int:pk>/', LessonDetailView.as_view(), name='lesson_detail'),
    path('lesson/api/<int:lesson_id>/', lesson_detail, name='lesson_api_detail'),
    path('lesson/mark_complete/<int:lesson_id>/',
         mark_lesson_complete, name='mark_lesson_complete'),
]
