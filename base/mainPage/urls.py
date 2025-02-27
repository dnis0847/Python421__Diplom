from django.urls import path
from .views import IndexView, AboutView, ContactsView
app_name = 'mainPage'

urlpatterns = [
    path('', IndexView.as_view(), name="home"),
    path('about', AboutView.as_view(), name="about"),
    path('contacts', ContactsView.as_view(), name="contacts"),
]
