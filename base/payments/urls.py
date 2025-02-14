# base/payments/urls.py
from django.urls import path
from .views import SimulatePaymentView

urlpatterns = [
    path('simulate-payment/<int:course_id>/', SimulatePaymentView.as_view(), name='simulate_payment'),
]