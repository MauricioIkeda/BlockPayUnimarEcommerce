from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid


class Categoria(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class Subcategoria(models.Model):
    nome = models.CharField(max_length=50)
    categoria_pai = models.ForeignKey(
        Categoria, related_name="subcategorias", on_delete=models.CASCADE, default=1
    )

    def __str__(self):
        return f"{self.nome} - {self.categoria_pai}"


class Produto(models.Model):
    nome = models.CharField(max_length=50)
    preco = models.DecimalField(default=0, decimal_places=2, max_digits=6)
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, default=1)
    descricao = models.CharField(max_length=255, default="", blank=True, null=True)
    quantidade = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    imagem = models.ImageField(upload_to="uploads/produtos/")
    vendedor = models.ForeignKey(
        User, related_name="produtos", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.nome


class Carrinho(models.Model):
    usuario = models.OneToOneField(
        User, related_name="carrinho", on_delete=models.CASCADE
    )

    def total(self):
        return sum(item.subtotal() for item in self.itens.all())


class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(
        Carrinho, related_name="itens", on_delete=models.CASCADE
    )
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=0)

    def subtotal(self):
        return self.produto.preco * self.quantidade


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendedor = models.ForeignKey(
        User, related_name="order_seller", on_delete=models.CASCADE
    )
    comprador = models.ForeignKey(
        User, related_name="order_buyer", on_delete=models.CASCADE
    )
    valor_total_pedido = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status_pagamento = models.CharField(max_length=50, default="pendente")
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {str(self.id)} - {self.comprador.username}"

    # Esta propriedade recalcula o total baseado nos itens, garantindo consistência.
    @property
    def calcular_valor_total(self):
        return sum(item.subtotal for item in self.itens.all())


class ItemOrder(models.Model):
    order = models.ForeignKey(Order, related_name="itens", on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    preco = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Preço no momento da compra

    @property
    def subtotal(self):
        return self.quantidade * self.preco

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade} unidades"


class Solicitacao_Vendedor(models.Model):
    usuario = models.ForeignKey(
        User, related_name="solicitacao_vendedor", on_delete=models.CASCADE
    )
    nome_completo = models.CharField(max_length=75, null=False, blank=False)
    cpf = models.CharField(max_length=75, null=False, blank=False)
    descricao = models.CharField(max_length=500, null=False, blank=False)

    def __str__(self):
        return f"({self.cpf}) {self.nome_completo}"
