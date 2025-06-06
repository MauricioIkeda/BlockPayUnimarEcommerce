import decimal
from unittest import mock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import (
    Categoria,
    Produto,
    Carrinho,
    ItemCarrinho,
    Order,
    ItemOrder,
    Subcategoria,
)
from Usuario.models import Profile

import json
from django.contrib.messages import get_messages
from django.http import JsonResponse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q


class StoreModelsTest(TestCase):
    def setUp(self):
        self.vendedor = User.objects.create_user(
            username="vendedor_test", password="123"
        )
        self.comprador = User.objects.create_user(
            username="comprador_test", password="123"
        )
        self.categoria = Categoria.objects.create(nome="Eletrônicos")
        self.subcategoria = Subcategoria.objects.create(
            nome="Teclados", categoria_pai=self.categoria
        )

        self.produto1 = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=self.subcategoria,
            nome="Teclado",
            preco=decimal.Decimal("150.75"),
            quantidade=10,
        )
        self.produto2 = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=self.subcategoria,
            nome="Mouse",
            preco=decimal.Decimal("50.00"),
            quantidade=5,
        )

    def test_carrinho_e_item_carrinho_subtotal_e_total(self):
        carrinho, _ = Carrinho.objects.get_or_create(usuario=self.comprador)
        item1 = ItemCarrinho.objects.create(
            carrinho=carrinho, produto=self.produto1, quantidade=2
        )
        item2 = ItemCarrinho.objects.create(
            carrinho=carrinho, produto=self.produto2, quantidade=1
        )

        self.assertEqual(item1.subtotal(), decimal.Decimal("301.50"))
        self.assertEqual(carrinho.total(), decimal.Decimal("351.50"))

    def test_order_calcular_valor_total(self):
        order = Order.objects.create(vendedor=self.vendedor, comprador=self.comprador)
        ItemOrder.objects.create(
            order=order, produto=self.produto1, quantidade=3, preco=self.produto1.preco
        )
        ItemOrder.objects.create(
            order=order, produto=self.produto2, quantidade=4, preco=self.produto2.preco
        )

        self.assertEqual(order.calcular_valor_total, decimal.Decimal("652.25"))


class StoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.vendedor = User.objects.create_user(
            username="vendedor_view", password="123"
        )
        self.comprador = User.objects.create_user(
            username="comprador_view", password="123"
        )
        self.vendedor.perfil.mp_access_token = "TEST_ACCESS_TOKEN_FOR_SELLER"
        self.vendedor.perfil.mp_connected = True
        self.vendedor.perfil.save()

        self.comprador.perfil.mp_access_token = "TEST_ACCESS_TOKEN_FOR_BUYER"
        self.comprador.perfil.mp_connected = True
        self.comprador.perfil.save()

        self.categoria = Categoria.objects.create(nome="View Tests")
        self.subcategoria = Subcategoria.objects.create(
            nome="Monitores", categoria_pai=self.categoria
        )

        image_file = SimpleUploadedFile(
            "test.jpg", b"fake_image_data", content_type="image/jpeg"
        )

        self.produto = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=self.subcategoria,
            nome="Monitor Gamer",
            preco=1200.00,
            quantidade=3,
            imagem=image_file,
        )

        image_file_2 = SimpleUploadedFile(
            "test2.jpg", b"fake_image_data", content_type="image/jpeg"
        )
        self.produto_webhook = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=self.subcategoria,
            nome="Headset",
            preco=300.00,
            quantidade=10,
            imagem=image_file_2,
        )
        self.order = Order.objects.create(
            vendedor=self.vendedor, comprador=self.comprador, status_pagamento="pending"
        )
        Carrinho.objects.get_or_create(usuario=self.comprador)
        self.item = ItemOrder.objects.create(
            order=self.order, produto=self.produto_webhook, quantidade=2, preco=300.00
        )
        self.order_id = str(self.order.id)

    def test_view_sobre_carrega_corretamente(self):
        url = reverse("sobre")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "sobre.html")

    def test_add_remover_excluir_carrinho(self):
        """Testa o fluxo completo de manipulação do carrinho via views."""
        self.client.login(username="comprador_view", password="123")

        Carrinho.objects.filter(usuario=self.comprador).delete()
        self.assertFalse(Carrinho.objects.filter(usuario=self.comprador).exists())

        self.client.get(reverse("adicionar_carrinho", args=[self.produto.id, 2]))
        self.assertTrue(Carrinho.objects.filter(usuario=self.comprador).exists())
        carrinho = Carrinho.objects.get(usuario=self.comprador)
        self.assertEqual(carrinho.itens.count(), 1)
        item = carrinho.itens.first()
        self.assertEqual(item.quantidade, 2)
        self.client.get(reverse("remover_carrinho", args=[self.produto.id]))
        item.refresh_from_db()
        self.assertEqual(item.quantidade, 1)
        self.client.get(reverse("excluir_carrinho", args=[self.produto.id]))
        self.assertEqual(carrinho.itens.count(), 0)

    @mock.patch("Store.views.realizar_pagamento")
    def test_view_pagamento_cria_order_corretamente(self, mock_pagamento):
        mock_pagamento.return_value = reverse("compra_success")
        self.client.login(username="comprador_view", password="123")

        carrinho, _ = Carrinho.objects.get_or_create(usuario=self.comprador)
        ItemCarrinho.objects.create(
            carrinho=carrinho, produto=self.produto, quantidade=1
        )

        order_count_before = Order.objects.count()

        response = self.client.post(reverse("pagamento", args=[self.vendedor.id]))

        order_count_after = Order.objects.count()

        self.assertEqual(order_count_after, order_count_before + 1)

        order = Order.objects.last()
        self.assertEqual(order.vendedor, self.vendedor)
        self.assertEqual(order.comprador, self.comprador)
        mock_pagamento.assert_called_once()
        self.assertRedirects(
            response, reverse("compra_success"), fetch_redirect_response=False
        )

    @mock.patch("Store.views.mercadopago.SDK")
    def test_webhook_success_approved(self, mock_sdk_class):
        mock_sdk = mock_sdk_class.return_value
        mock_sdk.payment().get.return_value = {
            "status": 200,
            "response": {"status": "approved", "external_reference": self.order_id},
        }
        response = self.client.post(
            reverse("mercadopago_webhook"),
            data=json.dumps({"data": {"id": "pagamento123"}, "type": "payment"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.produto_webhook.refresh_from_db()
        self.assertEqual(self.order.status_pagamento, "approved")
        self.assertEqual(self.produto_webhook.quantidade, 8)
        self.assertJSONEqual(response.content, {"status": "ok"})

    def test_webhook_sem_payment_id(self):
        response = self.client.post(
            reverse("mercadopago_webhook"),
            data=json.dumps({"data": {}, "type": "payment"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"status": "error", "message": "ID de pagamento não encontrado"},
        )

    @mock.patch("Store.views.mercadopago.SDK")
    def test_webhook_payment_not_found_mp(self, mock_sdk_class):
        """
        Testa o comportamento do webhook quando o Mercado Pago retorna
        um status diferente de 200 (ex: 404) para a requisição de pagamento.
        """
        mock_sdk = mock_sdk_class.return_value
        mock_sdk.payment().get.return_value = {
            "status": 404,
            "response": {},
        }

        response = self.client.post(
            reverse("mercadopago_webhook"),
            data=json.dumps(
                {"data": {"id": "non_existent_payment"}, "type": "payment"}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            response.content,
            {"status": "error", "message": "Pagamento não encontrado no Mercado Pago"},
        )

    def test_compra_success_view(self):
        response = self.client.get(reverse("compra_success"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "compra_success.html")

    def test_compra_failure_view(self):
        response = self.client.get(reverse("compra_failure"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "compra_failure.html")

    def test_compra_pending_view(self):
        response = self.client.get(reverse("compra_pending"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "compra_pending.html")

    def test_produto_view_get(self):
        url = reverse("pagina_produto", args=[self.produto.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "produto.html")
        self.assertIn("produto", response.context)
        self.assertEqual(response.context["produto"], self.produto)

    def test_produto_view_post_autenticado(self):
        self.client.login(username="comprador_view", password="123")
        url = reverse("pagina_produto", args=[self.produto.id])
        response = self.client.post(url, {"quantidade": 2})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "produto.html")
        carrinho = Carrinho.objects.get(usuario=self.comprador)
        item = carrinho.itens.first()
        self.assertEqual(item.produto, self.produto)
        self.assertEqual(item.quantidade, 2)

    def test_produto_view_post_nao_autenticado(self):
        url = reverse("pagina_produto", args=[self.produto.id])
        response = self.client.post(url, {"quantidade": 1})
        self.assertRedirects(response, reverse("logar"))

    def test_carrinho_view_autenticado(self):
        self.client.login(username="comprador_view", password="123")
        url = reverse("carrinho")

        carrinho_usuario, _ = Carrinho.objects.get_or_create(usuario=self.comprador)

        ItemCarrinho.objects.create(
            carrinho=carrinho_usuario, produto=self.produto, quantidade=2
        )

        vendedor_2 = User.objects.create_user(username="vendedor_2", password="123")
        categoria_2 = Categoria.objects.create(nome="Livros")
        subcategoria_2 = Subcategoria.objects.create(
            nome="Ficção", categoria_pai=categoria_2
        )

        image_file_vendedor_2 = SimpleUploadedFile(
            "test_vendedor2.jpg", b"fake_image_data_2", content_type="image/jpeg"
        )

        produto_vendedor_2 = Produto.objects.create(
            vendedor=vendedor_2,
            subcategoria=subcategoria_2,
            nome="Livro A",
            preco=decimal.Decimal("50.00"),
            quantidade=5,
            imagem=image_file_vendedor_2,
        )
        ItemCarrinho.objects.create(
            carrinho=carrinho_usuario, produto=produto_vendedor_2, quantidade=3
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "carrinho.html")
        self.assertIn("itens_por_vendedor", response.context)

        itens_por_vendedor = response.context["itens_por_vendedor"]

        self.assertIn(self.vendedor, itens_por_vendedor)
        self.assertIn(vendedor_2, itens_por_vendedor)

        self.assertEqual(len(itens_por_vendedor[self.vendedor]["itens"]), 1)
        self.assertEqual(
            itens_por_vendedor[self.vendedor]["subtotal"],
            decimal.Decimal("2400.00"),
        )
        self.assertEqual(
            itens_por_vendedor[self.vendedor]["itens"][0].produto.nome, "Monitor Gamer"
        )
        self.assertEqual(itens_por_vendedor[self.vendedor]["itens"][0].quantidade, 2)

        self.assertEqual(len(itens_por_vendedor[vendedor_2]["itens"]), 1)
        self.assertEqual(
            itens_por_vendedor[vendedor_2]["subtotal"],
            decimal.Decimal("150.00"),
        )
        self.assertEqual(
            itens_por_vendedor[vendedor_2]["itens"][0].produto.nome, "Livro A"
        )
        self.assertEqual(itens_por_vendedor[vendedor_2]["itens"][0].quantidade, 3)

        self.assertIn("total_carrinho", response.context)
        self.assertEqual(
            response.context["total_carrinho"],
            decimal.Decimal("2550.00"),
        )

    def test_carrinho_view_nao_autenticado(self):
        self.client.logout()

        url = reverse("carrinho")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("logar"))

        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Você deve estar logado para acessar o carrinho"
        )
        self.assertEqual(messages[0].tags, "error")

    def test_home_view(self):
        url = reverse("home")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertIn("produtos", response.context)
        self.assertIn(self.produto, response.context["produtos"])

    def test_adicionar_carrinho_quantidade_maior_que_estoque(self):
        self.client.login(username="comprador_view", password="123")

        carrinho, _ = Carrinho.objects.get_or_create(usuario=self.comprador)
        carrinho.itens.all().delete()

        url = reverse("adicionar_carrinho", args=[self.produto.id, 10])
        self.client.get(url)

        carrinho.refresh_from_db()
        item = carrinho.itens.first()

        self.assertEqual(item.quantidade, self.produto.quantidade)

    def test_remover_carrinho_sem_carrinho_existente(self):
        self.client.login(username="comprador_view", password="123")

        Carrinho.objects.filter(usuario=self.comprador).delete()

        response = self.client.get(reverse("remover_carrinho", args=[self.produto.id]))
        self.assertRedirects(response, reverse("carrinho"))

    def test_remover_carrinho_quantidade_igual_a_um(self):
        self.client.login(username="comprador_view", password="123")

        carrinho, _ = Carrinho.objects.get_or_create(usuario=self.comprador)
        carrinho.itens.all().delete()

        ItemCarrinho.objects.create(
            carrinho=carrinho, produto=self.produto, quantidade=1
        )

        self.client.get(reverse("remover_carrinho", args=[self.produto.id]))

        carrinho.refresh_from_db()
        self.assertEqual(carrinho.itens.count(), 0)

    # --- Testes para a view categoria ---

    def test_categoria_view_filtra_por_subcategoria(self):
        categoria_nova = Categoria.objects.create(nome="Esportes")
        subcategoria_nova = Subcategoria.objects.create(
            nome="Futebol", categoria_pai=categoria_nova
        )
        produto_futebol = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=subcategoria_nova,
            nome="Bola de Futebol",
            preco=decimal.Decimal("100.00"),
            quantidade=20,
            imagem=SimpleUploadedFile(
                "bola.jpg", b"fake_image", content_type="image/jpeg"
            ),
        )
        Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=self.subcategoria,
            nome="Teclado",
            preco=decimal.Decimal("200.00"),
            quantidade=15,
            imagem=SimpleUploadedFile(
                "teclado.jpg", b"fake_image", content_type="image/jpeg"
            ),
        )

        url = reverse("categoria", args=["Futebol"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home-category.html")
        self.assertIn("produtos", response.context)
        self.assertIn("categorias", response.context)

        self.assertEqual(len(response.context["produtos"]), 1)
        self.assertIn(produto_futebol, response.context["produtos"])
        self.assertNotIn(self.produto, response.context["produtos"])

    def test_categoria_view_filtra_por_categoria_pai(self):
        subcategoria_audio = Subcategoria.objects.create(
            nome="Áudio", categoria_pai=self.categoria
        )
        produto_audio = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=subcategoria_audio,
            nome="Fone de Ouvido",
            preco=decimal.Decimal("250.00"),
            quantidade=8,
            imagem=SimpleUploadedFile(
                "fone.jpg", b"fake_image", content_type="image/jpeg"
            ),
        )

        categoria_roupas = Categoria.objects.create(nome="Roupas")
        subcategoria_camisas = Subcategoria.objects.create(
            nome="Camisas", categoria_pai=categoria_roupas
        )
        produto_camisa = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=subcategoria_camisas,
            nome="Camisa Casual",
            preco=decimal.Decimal("80.00"),
            quantidade=30,
            imagem=SimpleUploadedFile(
                "camisa.jpg", b"fake_image", content_type="image/jpeg"
            ),
        )

        url = reverse("categoria", args=["View Tests"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home-category.html")
        self.assertIn("produtos", response.context)
        self.assertIn("categorias", response.context)

        self.assertIn(self.produto, response.context["produtos"])
        self.assertIn(self.produto_webhook, response.context["produtos"])
        self.assertIn(produto_audio, response.context["produtos"])

        self.assertNotIn(produto_camisa, response.context["produtos"])

        self.assertEqual(len(response.context["produtos"]), 3)

    def test_categoria_view_sem_produtos(self):
        url = reverse("categoria", args=["CategoriaInexistente"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home-category.html")
        self.assertIn("produtos", response.context)
        self.assertIn("categorias", response.context)
        self.assertEqual(
            len(response.context["produtos"]), 0
        )  # Nenhuma produto encontrado


class WebhookTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.vendedor = User.objects.create_user(
            username="vendedor_webhook", password="123"
        )
        self.comprador = User.objects.create_user(
            username="comprador_webhook", password="123"
        )

        self.vendedor.perfil.mp_access_token = "TEST_ACCESS_TOKEN_FOR_SELLER_WEBHOOK"
        self.vendedor.perfil.save()
        self.comprador.perfil.mp_access_token = "TEST_ACCESS_TOKEN_FOR_BUYER_WEBHOOK"
        self.comprador.perfil.save()

        self.categoria = Categoria.objects.create(nome="Webhook Test Category")
        self.subcategoria = Subcategoria.objects.create(
            nome="Webhook Subcategory", categoria_pai=self.categoria
        )
        self.produto_webhook = Produto.objects.create(
            vendedor=self.vendedor,
            subcategoria=self.subcategoria,
            nome="Produto Webhook",
            preco=100.00,
            quantidade=5,
            imagem=SimpleUploadedFile(
                "webhook_test.jpg", b"fake_data", content_type="image/jpeg"
            ),
        )
        self.order = Order.objects.create(
            vendedor=self.vendedor, comprador=self.comprador, status_pagamento="pending"
        )
        Carrinho.objects.get_or_create(usuario=self.comprador)
        ItemOrder.objects.create(
            order=self.order, produto=self.produto_webhook, quantidade=2, preco=100.00
        )
        self.order_id = str(self.order.id)

    @mock.patch("Store.views.mercadopago.SDK")
    def test_webhook_sem_external_reference(self, mock_sdk_class):
        """Garante que a ausência de external_reference é tratada corretamente."""
        mock_sdk = mock_sdk_class.return_value
        mock_sdk.payment().get.return_value = {
            "status": 200,
            "response": {
                "status": "approved",
            },
        }

        response = self.client.post(
            reverse("mercadopago_webhook"),
            data=json.dumps({"data": {"id": "123"}, "type": "payment"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"status": "error", "message": "Referência externa não encontrada"},
        )

    @mock.patch("Store.views.mercadopago.SDK")
    def test_webhook_status_update_non_approved(self, mock_sdk_class):
        mock_sdk = mock_sdk_class.return_value

        mock_sdk.payment().get.return_value = {
            "status": 200,
            "response": {"status": "in_process", "external_reference": self.order_id},
        }

        self.order.status_pagamento = "pending"
        self.order.save()

        response = self.client.post(
            reverse("mercadopago_webhook"),
            data=json.dumps(
                {"data": {"id": "pagamento_in_process"}, "type": "payment"}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()

        self.assertEqual(self.order.status_pagamento, "in_process")
        self.assertJSONEqual(response.content, {"status": "ok"})

    @mock.patch("Store.views.mercadopago.SDK")
    def test_webhook_order_does_not_exist(self, mock_sdk_class):
        """
        Testa o comportamento do webhook quando o Order (pedido)
        com o external_reference não é encontrado.
        """
        mock_sdk = mock_sdk_class.return_value

        invalid_order_id = "99999999-9999-9999-9999-999999999999"
        mock_sdk.payment().get.return_value = {
            "status": 200,
            "response": {"status": "approved", "external_reference": invalid_order_id},
        }

        response = self.client.post(
            reverse("mercadopago_webhook"),
            data=json.dumps(
                {"data": {"id": "pagamento_inexistente"}, "type": "payment"}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            response.content,
            {
                "status": "error",
                "message": f"Pedido com ID {invalid_order_id} não encontrado",
            },
        )

    @mock.patch("Store.views.mercadopago.SDK")
    def test_webhook_general_exception_handling(self, mock_sdk_class):
        mock_sdk = mock_sdk_class.return_value

        mock_sdk.payment().get.side_effect = Exception("Erro simulado do Mercado Pago")

        response = self.client.post(
            reverse("mercadopago_webhook"),
            data=json.dumps({"data": {"id": "any_payment_id"}, "type": "payment"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(
            response.content,
            {"status": "error", "message": "Erro interno do servidor"},
        )
