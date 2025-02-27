from django.urls import path
from .views import (
    RegisterView,
    UserLoginView,
    custom_logout,
    DashboardView,
    CourseDetailView,
    LessonDetailView,
    lesson_detail,
    mark_lesson_complete,
    add_review,
    delete_review,
    CourseEditView,
    CourseDeleteView,
    CourseCreateView,
    LessonCreateView,
    LessonEditView,
    LessonDeleteView
)


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
    path('course/<int:course_id>/review/', add_review, name='add_review'),
    path('course/<int:course_id>/delete_review/',
         delete_review, name='delete_review'),
    path('course/edit/<int:pk>/', CourseEditView.as_view(),
         name='course_edit_detail'),
    path('course/delete/<int:pk>/',
         CourseDeleteView.as_view(), name='course_delete'),
    path('course/create/', CourseCreateView.as_view(), name='course_create'),
    path('course/<int:course_id>/lesson/create/',
         LessonCreateView.as_view(), name='lesson_create'),
    path('course/<int:course_id>/lesson/edit/<int:pk>/',
         LessonEditView.as_view(), name='edit_lesson'),
    path('course/<int:course_id>/lesson/delete/<int:pk>/',
         LessonDeleteView.as_view(), name='delete_lesson'),
]
