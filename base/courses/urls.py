from django.urls import path
from .views import CoursesView, CourseDetailView, load_courses
from payments.views import SimulatePaymentView

app_name = 'courses'

urlpatterns = [
    path('', CoursesView.as_view(), name="courses"),
    path('load-courses/', load_courses, name='load_courses'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
]
