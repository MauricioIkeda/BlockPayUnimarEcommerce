from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("produto/<int:id_produto>", views.produto, name="pagina_produto"),
    path("carrinho/", views.carrinho, name="carrinho"),
    path(
        "carrinho/adicionar/<int:id_produto>/<int:quantidade>",
        views.adicionar_carrinho,
        name="adicionar_carrinho",
    ),
    path(
        "carrinho/remover/<int:id_produto>",
        views.remover_carrinho,
        name="remover_carrinho",
    ),
    path(
        "carrinho/excluir/<int:id_produto>",
        views.excluir_carrinho,
        name="excluir_carrinho",
    ),
    path("carrinho/pagamento/<int:vendedor_id>/", views.pagamento, name="pagamento"),
    path("carrinho/compra_realizada/", views.compra_success, name="compra_success"),
    path("carrinho/compra_falha/", views.compra_failure, name="compra_failure"),
    path("carrinho/compra_pendente/", views.compra_pending, name="compra_pending"),
    path("webhook/mercadopago/", views.mercadopago_webhook, name="mercadopago_webhook"),
    path("categoria/<str:nome_categoria>/", views.categoria, name="categoria"),
    path("sobre/", views.sobre, name="sobre"),
]
