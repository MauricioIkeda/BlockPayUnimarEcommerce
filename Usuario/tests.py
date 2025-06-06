# Usuario/tests.py

import os
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)  # Necessário para mock de arquivos
from django.conf import settings

# Importando os modelos das suas apps
from .models import Profile
from Store.models import (
    Solicitacao_Vendedor,
    Produto,
    Categoria,
    Subcategoria,
    Order,
    ItemOrder,
)


class UsuarioViewsTestCase(TestCase):
    """
    Suite de testes para as views da aplicação Usuario.
    """

    def setUp(self):
        """
        Configuração inicial que é executada antes de cada teste.
        Cria usuários (normal e staff), perfis e dados básicos necessários.
        """
        self.client = Client()

        # Cria um usuário comum para testes. O sinal deve criar o Profile automaticamente.
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123", first_name="Test"
        )

        # Cria um usuário administrador (staff) para testar views restritas.
        self.staff_user = User.objects.create_superuser(
            username="staffuser", password="staffpassword123", email="staff@test.com"
        )

        # Cria dados para a loja (Categoria e Subcategoria)
        self.categoria = Categoria.objects.create(nome="Eletrônicos")
        self.subcategoria = Subcategoria.objects.create(
            nome="Smartphones", categoria_pai=self.categoria
        )

        # Define URLs comuns para reutilização
        # Certifique-se de que os 'names' nas suas URLs correspondem a estes.
        self.cadastrar_url = reverse("cadastrar")
        self.logar_url = reverse("logar")
        self.deslogar_url = reverse("deslogar")
        self.home_url = reverse("home")
        self.perfil_url = reverse("perfil_user", args=[self.user.username])
        self.solicitar_vendedor_url = reverse("solicitar_vendedor")
        self.ver_solicitacao_url = reverse("ver_solicitacao")

    # --- Testes de Autenticação ---

    def test_cadastrar_view(self):
        """Testa a funcionalidade de cadastro de novos usuários."""
        # Teste GET
        response = self.client.get(self.cadastrar_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cadastrar.html")

        # Teste POST - Sucesso
        response = self.client.post(
            self.cadastrar_url,
            {
                "usuario": "newuser",
                "nome": "New",
                "senha1": "newpassword123",
                "senha2": "newpassword123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.logar_url)
        self.assertTrue(User.objects.filter(username="newuser").exists())

        # Teste POST - Senhas diferentes
        response = self.client.post(
            self.cadastrar_url,
            {
                "usuario": "anotheruser",
                "nome": "Another",
                "senha1": "password123",
                "senha2": "password456",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.cadastrar_url)
        self.assertFalse(User.objects.filter(username="anotheruser").exists())

        # Teste POST - Usuário já existe
        response = self.client.post(
            self.cadastrar_url,
            {
                "usuario": "testuser",
                "nome": "Test",
                "senha1": "testpassword123",
                "senha2": "testpassword123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.cadastrar_url)

    def test_logar_e_deslogar_view(self):
        """Testa o login e logout de um usuário."""
        # Teste POST - Login com sucesso
        response = self.client.post(
            self.logar_url, {"usuario": "testuser", "senha": "testpassword123"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Teste Deslogar
        response = self.client.get(self.deslogar_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

        # Teste POST - Login com falha
        response = self.client.post(
            self.logar_url, {"usuario": "testuser", "senha": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.logar_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # --- Testes de Perfil e Vendedor ---

    def test_perfil_view(self):
        """Testa a visualização da página de perfil."""
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.perfil_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "perfil_usuario.html")
        self.assertEqual(response.context["usuario"].username, "testuser")

    def test_editar_perfil_view(self):
        """Testa a edição do perfil do usuário."""
        self.client.login(username="testuser", password="testpassword123")
        edit_url = reverse("editar_perfil", args=[self.user.username])

        response = self.client.post(
            edit_url,
            {"nome": "Test User Edited", "bios": "This is my new bio.", "salvar": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.perfil_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Test User Edited")
        self.assertEqual(self.user.perfil.bios, "This is my new bio.")

    def test_excluir_conta_view(self):
        """Testa a exclusão da conta do usuário."""
        self.client.login(username="testuser", password="testpassword123")
        edit_url = reverse("editar_perfil", args=[self.user.username])

        response = self.client.post(edit_url, {"excluir": ""})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)

        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_solicitacao_vendedor_flow(self):
        """Testa o fluxo completo de solicitação, aprovação e recusa de vendedor."""
        # 1. Usuário solicita para ser vendedor
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.post(
            self.solicitar_vendedor_url,
            {
                "nome-completo": "Test User Full Name",
                "cpf": "123.456.789-00",
                "produtos-a-vender": "Eletrônicos diversos",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        self.assertTrue(Solicitacao_Vendedor.objects.filter(usuario=self.user).exists())

        # 2. Staff visualiza a solicitação
        self.client.login(username="staffuser", password="staffpassword123")
        response = self.client.get(self.ver_solicitacao_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ver_solicitacao.html")
        self.assertIn("solicitacoes", response.context)
        self.assertEqual(len(response.context["solicitacoes"]), 1)

        # 3. Staff aceita a solicitação
        aceitar_url = reverse("aceitar_solicitacao", args=[self.user.username])
        response = self.client.get(aceitar_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.ver_solicitacao_url)

        self.user.refresh_from_db()
        self.assertTrue(self.user.perfil.vendedor)
        self.assertFalse(
            Solicitacao_Vendedor.objects.filter(usuario=self.user).exists()
        )

        # 4. Teste de recusa (em um novo usuário)
        other_user = User.objects.create_user("otheruser", "otherpass")
        # CORREÇÃO: A linha abaixo foi removida, pois o sinal já cria o perfil.
        # Profile.objects.create(usuario=other_user)
        Solicitacao_Vendedor.objects.create(
            usuario=other_user, nome_completo="Other", cpf="987654", descricao="nada"
        )
        recusar_url = reverse("recusar_solicitacao", args=[other_user.username])
        self.client.get(recusar_url)
        other_user.refresh_from_db()
        self.assertFalse(other_user.perfil.vendedor)
        self.assertFalse(
            Solicitacao_Vendedor.objects.filter(usuario=other_user).exists()
        )

    # --- Testes de Gerenciamento de Produto ---

    def test_adicionar_produto_view(self):
        """Testa a view de adicionar um novo produto."""
        self.user.perfil.vendedor = True
        self.user.perfil.save()

        self.client.login(username="testuser", password="testpassword123")
        add_product_url = reverse("adicionar_produto", args=[self.user.username])

        image = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )

        response = self.client.post(
            add_product_url,
            {
                "nome": "Smartphone X",
                "descricao": "Um ótimo smartphone.",
                "preco": 1500.00,
                "quantidade_estoque": 10,
                "subcategoria": self.subcategoria.id,
                "imagem": image,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.perfil_url)
        self.assertTrue(
            Produto.objects.filter(nome="Smartphone X", vendedor=self.user).exists()
        )

    def test_editar_e_excluir_produto_view(self):
        """Testa a edição e exclusão de um produto."""
        self.user.perfil.vendedor = True
        self.user.perfil.save()

        # CORREÇÃO: Adicionamos uma imagem ao criar o produto para evitar o ValueError no redirect.
        image = SimpleUploadedFile(
            "original.jpg", b"file_content", content_type="image/jpeg"
        )
        produto = Produto.objects.create(
            vendedor=self.user,
            nome="Produto Original",
            preco=100.00,
            subcategoria=self.subcategoria,
            quantidade=5,
            imagem=image,
        )

        self.client.login(username="testuser", password="testpassword123")

        # Teste de Edição
        edit_product_url = reverse("editar_produto", args=[produto.id])
        response = self.client.post(
            edit_product_url,
            {
                "nome": "Produto Editado",
                "descricao": "Descrição editada.",
                "preco": "120.50",
                "quantidade_estoque": 3,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.perfil_url)

        produto.refresh_from_db()
        self.assertEqual(produto.nome, "Produto Editado")
        # Preços são Decimal, então a comparação deve ser com Decimal ou string
        self.assertEqual(str(produto.preco), "120.50")

        # Teste de Exclusão
        delete_product_url = reverse("excluir_produto", args=[produto.id])
        response = self.client.post(delete_product_url)
        lista_produtos_url = reverse("lista_produtos", args=[self.user.username])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, lista_produtos_url)
        self.assertFalse(Produto.objects.filter(id=produto.id).exists())

    # --- Testes de Vendas ---

    def test_vendas_view(self):
        """Testa a visualização da lista de vendas do usuário."""
        comprador = User.objects.create_user("comprador", "senhacomprador")
        Order.objects.create(
            vendedor=self.user, comprador=comprador, valor_total_pedido=100.00
        )

        self.client.login(username="testuser", password="testpassword123")
        vendas_url = reverse("vendas")
        response = self.client.get(vendas_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "vendas.html")
        self.assertIn("orders", response.context)
        self.assertEqual(len(response.context["orders"]), 1)

    # --- Testes de Integração com API (Mercado Pago) ---

    @patch("Usuario.views.os.getenv")
    def test_conectar_mercado_pago_redirect(self, mock_getenv):
        """Testa se o redirecionamento para a autorização do MP é gerado corretamente."""
        mock_getenv.return_value = "TEST_APP_ID"

        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(
            reverse("conectar_mp")
        )  # Assumindo name='conectar_mp'

        self.assertEqual(response.status_code, 302)
        self.assertIn("auth.mercadopago.com.br", response.url)
        self.assertIn("client_id=TEST_APP_ID", response.url)
        self.assertIn(f"state={self.user.id}", response.url)

    @patch("Usuario.views.requests.post")
    @patch("Usuario.views.os.getenv")
    def test_mercado_pago_callback_success(self, mock_getenv, mock_post):
        """Testa o callback do Mercado Pago em um cenário de sucesso."""
        mock_getenv.side_effect = ["TEST_CLIENT_SECRET", "TEST_APP_ID"]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "user_id": "mp_user_123",
        }
        mock_post.return_value = mock_response

        callback_url = (
            reverse("mp_callback") + f"?code=test_auth_code&state={self.user.id}"
        )
        response = self.client.get(callback_url)

        self.user.perfil.refresh_from_db()
        self.assertTrue(self.user.perfil.mp_connected)
        self.assertEqual(self.user.perfil.mp_access_token, "test_access_token")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.perfil_url)


# Adicione este código ao final do seu tests.py
# Ele contém os testes para as linhas que faltavam na cobertura.

from django.http import Http404
from unittest.mock import MagicMock


class UsuarioViewsCoverageTests(TestCase):
    """
    Suite de testes focada em aumentar a cobertura, testando os "caminhos infelizes"
    e lógicas condicionais que não foram executadas nos testes principais.
    """

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username="usera", password="passworda")
        self.user_b = User.objects.create_user(username="userb", password="passwordb")
        self.staff_user = User.objects.create_superuser(
            "staff", "staff@test.com", "passwordstaff"
        )

        self.user_b.perfil.vendedor = True
        self.user_b.perfil.save()

        self.categoria = Categoria.objects.create(nome="Roupas")
        self.subcategoria = Subcategoria.objects.create(
            nome="Camisetas", categoria_pai=self.categoria
        )

        image_file = SimpleUploadedFile(
            "produto_b.jpg", b"content", content_type="image/jpeg"
        )
        self.produto_b = Produto.objects.create(
            vendedor=self.user_b,
            nome="Produto do User B",
            preco=50.00,
            subcategoria=self.subcategoria,
            quantidade=10,
            imagem=image_file,
        )
        self.order = Order.objects.create(
            vendedor=self.user_b, comprador=self.user_a, valor_total_pedido=50
        )

    def test_unauthorized_access_paths(self):
        """
        Cobre linhas onde um usuário logado tenta acessar páginas de outro usuário.
        """
        self.client.login(username="usera", password="passworda")

        edit_perfil_url = reverse("editar_perfil", args=[self.user_b.username])
        response = self.client.get(edit_perfil_url)
        self.assertRedirects(response, reverse("home"))

        lista_produtos_url = reverse("lista_produtos", args=[self.user_b.username])
        response = self.client.get(lista_produtos_url)
        self.assertRedirects(response, reverse("home"))

        edit_produto_url = reverse("editar_produto", args=[self.produto_b.id])
        response = self.client.get(edit_produto_url)
        self.assertRedirects(response, reverse("home"))

        response = self.client.post(edit_produto_url, {"nome": "tentativa de hack"})
        self.assertRedirects(response, reverse("home"))

        # CORREÇÃO FINAL: Teste melhorado para fornecer uma mensagem de erro mais clara.
        vendas_details_url = reverse("vendas_details", args=[self.order.id])
        response = self.client.get(vendas_details_url)

        # A verificação agora é explícita. Se o status não for 404, o teste falha com uma
        # mensagem útil que informa o status que foi retornado.
        if response.status_code != 404:
            self.fail(
                f"Acesso a 'vendas_details' por usuário não autorizado deveria retornar 404 (Não Encontrado), "
                f"mas retornou {response.status_code}. "
                f"Por favor, verifique a condição 'if order.vendedor != request.user:' na sua view 'vendas_details'."
            )
        # Se o código for 404, o teste passa silenciosamente.
        self.assertEqual(response.status_code, 404)

    def test_authorized_vendas_details(self):
        """
        Garante que o vendedor pode ver os detalhes de sua própria venda.
        """
        self.client.login(username="userb", password="passwordb")
        vendas_details_url = reverse("vendas_details", args=[self.order.id])
        response = self.client.get(vendas_details_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "vendas_details.html")

    def test_profile_image_update(self):
        """
        Cobre o bloco de atualização de imagem de perfil, incluindo a remoção da antiga.
        """
        self.client.login(username="usera", password="passworda")

        self.user_a.perfil.foto.save(
            "old_pic.jpg", SimpleUploadedFile("old_pic.jpg", b"old")
        )
        self.assertTrue("old_pic" in self.user_a.perfil.foto.name)

        new_image = SimpleUploadedFile(
            "new_pic.jpg", b"new_content", content_type="image/jpeg"
        )
        edit_url = reverse("editar_perfil", args=[self.user_a.username])

        with patch("os.remove") as mock_remove:
            self.client.post(edit_url, {"foto_perfil": new_image, "salvar": ""})
            mock_remove.assert_called_once()

        self.user_a.perfil.refresh_from_db()
        self.assertTrue("new_pic" in self.user_a.perfil.foto.name)

    def test_add_product_failure_paths(self):
        """
        Testa falhas na adição de produtos: não logado, não é vendedor, sem subcategoria.
        """
        add_product_url = reverse("adicionar_produto", args=[self.user_a.username])

        response = self.client.get(add_product_url)
        self.assertRedirects(response, reverse("home"))

        self.client.login(username="usera", password="passworda")
        response = self.client.get(add_product_url)
        self.assertRedirects(response, reverse("home"))

        self.client.login(username="userb", password="passwordb")
        add_product_b_url = reverse("adicionar_produto", args=[self.user_b.username])
        response = self.client.post(
            add_product_b_url, {"nome": "Produto sem categoria"}
        )
        self.assertRedirects(response, add_product_b_url)

    def test_mercado_pago_failure_paths(self):
        """
        Cobre os cenários de falha na integração com o Mercado Pago.
        """
        conectar_mp_url = reverse("conectar_mp")
        response = self.client.get(conectar_mp_url)
        self.assertRedirects(response, reverse("logar"))

        self.client.login(username="usera", password="passworda")

        callback_url_no_code = reverse("mp_callback") + f"?state={self.user_a.id}"
        response = self.client.get(callback_url_no_code)
        self.assertRedirects(
            response, reverse("perfil_user", args=[self.user_a.username])
        )

        callback_url_invalid_state = (
            reverse("mp_callback") + "?code=testcode&state=9999"
        )
        response = self.client.get(callback_url_invalid_state)
        self.assertRedirects(response, reverse("home"))

        with patch("Usuario.views.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "invalid_grant"}
            mock_post.return_value = mock_response

            callback_url = (
                reverse("mp_callback") + f"?code=test_auth_code&state={self.user_a.id}"
            )
            response = self.client.get(callback_url)

            self.user_a.perfil.refresh_from_db()
            self.assertFalse(self.user_a.perfil.mp_connected)
            self.assertRedirects(
                response, reverse("perfil_user", args=[self.user_a.username])
            )
