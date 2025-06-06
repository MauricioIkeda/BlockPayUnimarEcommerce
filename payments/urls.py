# payments/urls.py
from django.urls import path
from .views import CreatePaymentView, CheckPaymentView

urlpatterns = [
    path('create_wallet/', CreatePaymentView.as_view()),  # Now under /api/create_wallet/
    path('create-payment/<int:payment_amount>/', CreatePaymentView.as_view(), name='create-payment'),
    path('check-payment/<int:payment_id>/', CheckPaymentView.as_view(), name='check-payment'),
]