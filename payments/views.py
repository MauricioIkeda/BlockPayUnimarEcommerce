from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from .models import Payment
from .services.bsc import get_usdt_balance
from .services.qr import generate_moonpay_link, generate_qr_base64
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from Store.models import Carrinho, ItemOrder, Order
from decimal import Decimal

def pagar_blockpay(request, vendedor_id):
    vendedor = get_object_or_404(User, id=vendedor_id)
    carrinho = get_object_or_404(Carrinho, usuario=request.user)

    itens_para_pagar = carrinho.itens.filter(produto__vendedor=vendedor)

    order = Order.objects.create(vendedor=vendedor, comprador=request.user)

    for item in itens_para_pagar:
        preco_item = Decimal(str(item.produto.preco))
        subtotal_item = item.quantidade * preco_item
        subtotal_vendedor += subtotal_item

    order.valor_total_pedido = subtotal_vendedor
    order.save()

    moonpay_link = generate_moonpay_link(
        vendedor.perfil.wallet_address, order.valor_total_pedido
    )
    
    return redirect(moonpay_link)

def checar_pagamento(request, payment_id):
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