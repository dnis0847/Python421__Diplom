from django.urls import path
from .views import RegisterView, UserLoginView
from users.views import custom_logout

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),
]