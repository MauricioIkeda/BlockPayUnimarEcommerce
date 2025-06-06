# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('pay/<int:vendedor_id>/', views.pagar_blockpay, name='pay'),
    path('check-payment/<int:payment_id>/', views.checar_pagamento, name='check-payment'),
]
