# payments/urls.py
from django.urls import path
from .views import CheckPaymentView, PayView

urlpatterns = [
    path('pay/<uuid:order_id>/', PayView.as_view(), name='pay'),
    path('check-payment/<int:payment_id>/', CheckPaymentView.as_view(), name='check-payment'),
]
