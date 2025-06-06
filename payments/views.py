from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from .models import Payment
from .services.bsc import get_usdt_balance
from .services.qr import generate_moonpay_link, generate_qr_base64
from Store.models import Order

class PayView(View):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Pedido não encontrado"}, status=404)

        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'seller': order.vendedor,
                'initial_balance': get_usdt_balance(order.vendedor.perfil.wallet_address),
                'amount_brl': order.valor_total_pedido,
            }
        )

        moonpay_link = generate_moonpay_link(
            order.vendedor.perfil.wallet_address, order.valor_total_pedido
        )
        qr_code = generate_qr_base64(moonpay_link)

        context = {
            "payment": payment,
            "moonpay_link": moonpay_link,
            "qr_code": qr_code,
            "wallet_address": order.vendedor.perfil.wallet_address,
            "amount_brl": order.valor_total_pedido,
        }
        return render(request, "pagamento.html", context)

class CheckPaymentView(View):
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Pagamento não encontrado"}, status=404)

        balance = get_usdt_balance(payment.seller.perfil.wallet_address)

        if balance > payment.initial_balance:
            payment.status = "completed"
            payment.save()
            payment.order.status_pagamento = "pago"
            payment.order.save()

        return JsonResponse({
            "payment_id": payment.id,
            "wallet_address": payment.seller.perfil.wallet_address,
            "usdt_balance": float(balance),
            "status": payment.status
        })
