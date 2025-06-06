from django.shortcuts import render, redirect
from .models import Produto
from .models import Produto, Categoria, Carrinho, ItemCarrinho, Order, ItemOrder
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from collections import defaultdict

from apimercadopago import realizar_pagamento
from dotenv import load_dotenv
import os
import mercadopago
from decimal import Decimal

from django.db.models import Q


def home(request):
    produtos = Produto.objects.all()
    categorias = Categoria.objects.all()

    return render(
        request, "home.html", {"produtos": produtos, "categorias": categorias}
    )


def sobre(request):
    return render(request, "sobre.html")


def produto(request, id_produto):
    produto = get_object_or_404(Produto, id=id_produto)

    if request.method == "GET":
        return render(request, "produto.html", {"produto": produto})
    elif request.method == "POST":
        if request.user.is_authenticated:
            quantidade = int(request.POST.get("quantidade", 1))
            adicionar_carrinho(request, produto.id, quantidade)
            return render(request, "produto.html", {"produto": produto})
        else:
            messages.error(request, ("Você deve estar logado para acessar o carrinho"))
            return redirect("logar")


def categoria(request, nome_categoria):
    filtro_subcategoria = Q(subcategoria__nome__iexact=nome_categoria)
    filtro_categoria_pai = Q(subcategoria__categoria_pai__nome__iexact=nome_categoria)

    produtos = Produto.objects.filter(
        filtro_subcategoria | filtro_categoria_pai
    ).distinct()

    categorias = Categoria.objects.all()

    return render(
        request, "home-category.html", {"produtos": produtos, "categorias": categorias}
    )


def carrinho(request):
    if not request.user.is_authenticated:
        messages.error(request, ("Você deve estar logado para acessar o carrinho"))
        return redirect("logar")

    try:
        carrinho_usuario = request.user.carrinho
        itens_do_carrinho = carrinho_usuario.itens.all()
    except Carrinho.DoesNotExist:
        itens_do_carrinho = []

    if not itens_do_carrinho:
        return render(request, "carrinho.html", {"itens_por_vendedor": {}})

    itens_por_vendedor = defaultdict(lambda: {"itens": [], "subtotal": Decimal("0.00")})
    for item in itens_do_carrinho:
        vendedor = item.produto.vendedor
        subtotal_item = item.subtotal()

        itens_por_vendedor[vendedor]["itens"].append(item)
        itens_por_vendedor[vendedor]["subtotal"] += subtotal_item

    contexto = {
        "usuario": request.user,
        "itens_por_vendedor": dict(itens_por_vendedor),
        "total_carrinho": carrinho_usuario.total(),
    }

    return render(request, "carrinho.html", contexto)


def adicionar_carrinho(request, id_produto, quantidade):
    produto = Produto.objects.get(id=id_produto)
    carrinho, criou = Carrinho.objects.get_or_create(usuario=request.user)
    item, criou = ItemCarrinho.objects.get_or_create(carrinho=carrinho, produto=produto)

    if item.quantidade + quantidade <= produto.quantidade:
        item.quantidade += quantidade
        item.save()
    else:
        item.quantidade = produto.quantidade
        item.save()

    return redirect("carrinho")


def remover_carrinho(request, id_produto):
    produto = Produto.objects.get(id=id_produto)

    carrinho = Carrinho.objects.filter(usuario=request.user).first()
    if not carrinho:
        return redirect("carrinho")

    item = ItemCarrinho.objects.filter(carrinho=carrinho, produto=produto).first()
    if item:
        if item.quantidade > 1:
            item.quantidade -= 1
            item.save()
        else:
            item.delete()

    return redirect("carrinho")


def excluir_carrinho(request, id_produto):
    produto = Produto.objects.get(id=id_produto)

    carrinho = Carrinho.objects.filter(usuario=request.user).first()

    item = ItemCarrinho.objects.filter(carrinho=carrinho, produto=produto).first()
    if item:
        item.delete()
    return redirect("carrinho")


def pagamento(request, vendedor_id):
    vendedor = get_object_or_404(User, id=vendedor_id)
    carrinho = get_object_or_404(Carrinho, usuario=request.user)

    seller_token = vendedor.perfil.mp_access_token

    print(
        f"--- DEBUG PAGAMENTO (Store/views.py - Seller Token Model): Para vendedor ID {vendedor_id} ({vendedor.username}), "
        f"o valor de seller_token (vendedor.perfil.mp_access_token) é: '{seller_token}' ---"
    )

    if not seller_token:
        messages.error(
            request,
            f"O vendedor '{vendedor.first_name}' não está configurado para receber pagamentos (token ausente).",
        )
        return redirect("carrinho")

    if not vendedor.perfil.mp_connected:
        messages.error(
            request,
            f"A conta Mercado Pago do vendedor '{vendedor.first_name}' não está corretamente conectada.",
        )
        return redirect("carrinho")

    itens_para_pagar = carrinho.itens.filter(produto__vendedor=vendedor)

    if not itens_para_pagar.exists():
        messages.error(request, "Itens não encontrados no carrinho para este vendedor.")
        return redirect("carrinho")

    MARKETPLACE_FEE_PERCENTAGE = Decimal("0.10")
    payment_items = []
    subtotal_vendedor = Decimal("0.00")

    order = Order.objects.create(vendedor=vendedor, comprador=request.user)

    for item in itens_para_pagar:
        preco_item = Decimal(str(item.produto.preco))
        subtotal_item = item.quantidade * preco_item
        subtotal_vendedor += subtotal_item

        ItemOrder.objects.create(
            order=order,
            produto=item.produto,
            quantidade=item.quantidade,
            preco=preco_item,
        )
        payment_items.append(
            {
                "id": str(item.produto.id),
                "title": item.produto.nome,
                "quantity": item.quantidade,
                "currency_id": "BRL",
                "unit_price": float(preco_item),
            }
        )

    order.valor_total_pedido = subtotal_vendedor
    order.save()

    comissao_total = round(subtotal_vendedor * MARKETPLACE_FEE_PERCENTAGE, 2)
    external_reference = str(order.id)

    try:
        link_pagamento = realizar_pagamento(
            seller_token,
            payment_items,
            external_reference,
            comissao_total,
        )
    except Exception as e:
        messages.error(request, f"Erro ao gerar link de pagamento: {e}")
        print(
            f"ERRO na view pagamento (Store/views.py - Seller Token Model) ao chamar realizar_pagamento: {e}"
        )
        return redirect("carrinho")

    itens_para_pagar.delete()

    return redirect(link_pagamento)


@csrf_exempt
def mercadopago_webhook(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Método não permitido"}, status=405
        )

    data = json.loads(request.body)

    if data.get("type") != "payment":
        return JsonResponse({"status": "ok", "message": "Não é um evento de pagamento"})

    payment_id = data.get("data", {}).get("id")
    if not payment_id:
        return JsonResponse(
            {"status": "error", "message": "ID de pagamento não encontrado"}, status=400
        )

    try:
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        payment_info = sdk.payment().get(payment_id)

        if payment_info["status"] != 200:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Pagamento não encontrado no Mercado Pago",
                },
                status=404,
            )

        response_data = payment_info["response"]
        payment_status = response_data.get("status")
        external_reference = response_data.get("external_reference")

        if not external_reference:
            return JsonResponse(
                {"status": "error", "message": "Referência externa não encontrada"},
                status=400,
            )

        pedido = Order.objects.get(id=external_reference)

        if payment_status == "approved" and pedido.status_pagamento != "approved":

            pedido.status_pagamento = "approved"
            pedido.save()

            for item_pedido in pedido.itens.all():
                produto = item_pedido.produto
                if produto.quantidade >= item_pedido.quantidade:
                    produto.quantidade -= item_pedido.quantidade
                    produto.save()
                else:
                    print(
                        f"Alerta: Estoque insuficiente para o produto {produto.id} no pedido {pedido.id}"
                    )

            carrinho_usuario = pedido.comprador.carrinho
            ids_produtos_no_pedido = [item.produto.id for item in pedido.itens.all()]
            ItemCarrinho.objects.filter(
                carrinho=carrinho_usuario, produto_id__in=ids_produtos_no_pedido
            ).delete()

        elif pedido.status_pagamento != payment_status:
            pedido.status_pagamento = payment_status
            pedido.save()

    except Order.DoesNotExist:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Pedido com ID {external_reference} não encontrado",
            },
            status=404,
        )
    except Exception as e:
        print(f"Erro inesperado no webhook: {e}")
        return JsonResponse(
            {"status": "error", "message": "Erro interno do servidor"}, status=500
        )

    return JsonResponse({"status": "ok"})


def compra_success(request):
    return render(request, "compra_success.html", {})


def compra_failure(request):
    return render(request, "compra_failure.html", {})


def compra_pending(request):
    return render(request, "compra_pending.html", {})
