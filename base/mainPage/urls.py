from django.urls import path
from .views import IndexView
app_name = 'mainPage'

urlpatterns = [
    path('', IndexView.as_view(), name="home"),
]
