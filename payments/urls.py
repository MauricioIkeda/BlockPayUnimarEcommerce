# payments/urls.py
from django.urls import path
from .views import CreatePaymentView, CheckPaymentView

urlpatterns = [
    path('pay/<uuid:order_id>/', CreatePaymentView.as_view(), name='payment'),
    path('check-payment/<int:payment_id>/', CheckPaymentView.as_view(), name='check-payment'),
]
