# Store/admin.py
from django.contrib import admin
from .models import (
    Categoria,
    Produto,
    Order,
    ItemOrder,
    Carrinho,
    ItemCarrinho,
    Solicitacao_Vendedor,
    Subcategoria,
)

# Registre todos os seus modelos de loja aqui
admin.site.register(Categoria)
admin.site.register(Subcategoria)
admin.site.register(Produto)
admin.site.register(Order)
admin.site.register(ItemOrder)
admin.site.register(Carrinho)
admin.site.register(ItemCarrinho)
admin.site.register(Solicitacao_Vendedor)
