from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Profile
from Store.models import Categoria, Subcategoria
from Store.models import Produto, Order, Solicitacao_Vendedor
from django.core.files.storage import FileSystemStorage
import os
from django.http import Http404
import requests
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings


def cadastrar(request):
    if request.method == "GET":
        return render(request, "cadastrar.html")
    elif request.method == "POST":
        username = request.POST.get("usuario")
        nome = request.POST.get("nome")
        password1 = request.POST.get("senha1")
        password2 = request.POST.get("senha2")
        if password1 != password2:
            messages.error(request, ("Senhas diferentes! tente novamente!"))
            return redirect("cadastrar")
        else:
            user = User.objects.filter(username=username)

            if user:
                messages.error(
                    request, ("O username já está cadastrado, tente novamente!")
                )
                return redirect("cadastrar")

            user = User.objects.create_user(
                username=username, password=password1, first_name=nome
            )
            user.save()

            messages.success(request, ("Cadastrado com sucesso! Faça seu login!"))
            return redirect("logar")


def logar(request):
    if request.method == "GET":
        return render(request, "logar.html")
    elif request.method == "POST":
        usuario = request.POST.get("usuario")
        senha = request.POST.get("senha")
        user = authenticate(request, username=usuario, password=senha)

        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, ("Usuario ou senha incorreto, tente novamente!"))
            return redirect("logar")


def deslogar(request):
    logout(request)
    return redirect("home")


def solicitar_vendedor(request):
    if request.method == "GET":
        return render(request, "solicitar_vendedor.html")
    elif request.method == "POST":
        if Solicitacao_Vendedor.objects.filter(usuario=request.user).exists():
            messages.error(
                request, ("Você ja mandou solicitação! Aguarde a verificação!")
            )
            return redirect("home")
        else:
            nome_completo = request.POST.get("nome-completo")
            cpf = request.POST.get("cpf")
            descricao = request.POST.get("produtos-a-vender")

            solicitacao = Solicitacao_Vendedor.objects.create(
                usuario=request.user,
                nome_completo=nome_completo,
                cpf=cpf,
                descricao=descricao,
            )
            solicitacao.save()

            messages.success(
                request, ("Solicitado com sucesso, aguarde até darmos uma resposta!")
            )
            return redirect("home")


@staff_member_required
def ver_solicitacao(request):
    solicitacoes = Solicitacao_Vendedor.objects.all()
    return render(request, "ver_solicitacao.html", {"solicitacoes": solicitacoes})


@staff_member_required
def aceitar_solicitacao(request, username):
    user = get_object_or_404(User, username=username)
    user = User.objects.get(username=username)
    user.perfil.vendedor = True
    user.perfil.save()

    solicitacao = Solicitacao_Vendedor.objects.get(usuario=user)
    solicitacao.delete()

    return redirect("ver_solicitacao")


@staff_member_required
def recusar_solicitacao(request, username):
    user = User.objects.get(username=username)
    user.perfil.vendedor = False
    user.perfil.save()

    solicitacao = Solicitacao_Vendedor.objects.get(usuario=user)
    solicitacao.delete()
    return redirect("ver_solicitacao")


def perfil(request, username):
    usuario = User.objects.get(username=username)

    return render(request, "perfil_usuario.html", {"usuario": usuario})


def editar_perfil(request, username):
    usuario = User.objects.get(username=username)

    if request.method == "GET":
        if request.user.username == username:
            return render(request, "editar_perfil.html", {"usuario": usuario})
        else:
            return redirect("home")

    elif request.method == "POST":
        if "salvar" in request.POST:
            nome = request.POST.get("nome")
            bios = request.POST.get("bios")
            imagem = request.FILES.get("foto_perfil")

            if nome:
                usuario.first_name = nome
                usuario.save()

            if bios:
                usuario.perfil.bios = bios

            if imagem:
                perfil = usuario.perfil
                caminho_imagem_default = perfil._meta.get_field("foto").default

                if perfil.foto and perfil.foto.name != caminho_imagem_default:
                    if os.path.isfile(perfil.foto.path):
                        os.remove(perfil.foto.path)
                fs = FileSystemStorage(
                    location="media/uploads/fotos_perfil/",
                    base_url="/media/uploads/fotos_perfil/",
                )
                filename = fs.save(imagem.name, imagem)
                usuario.perfil.foto = "uploads/fotos_perfil/" + filename

            usuario.perfil.save()

            return redirect("perfil_user", username=username)
        elif "excluir" in request.POST:
            perfil = usuario.perfil
            caminho_imagem_default = perfil._meta.get_field("foto").default

            if perfil.foto and perfil.foto.name != caminho_imagem_default:
                if os.path.isfile(perfil.foto.path):
                    os.remove(perfil.foto.path)

            user = request.user
            user.delete()
            logout(request)
            return redirect("home")


def lista_produtos(request, username):
    usuario = get_object_or_404(User, username=username)

    if request.user.username == username:
        return render(
            request,
            "lista_produtos.html",
            {"usuario": usuario, "usuariousername": username},
        )
    else:
        return redirect("home")


def editar_produto(request, id_produto):
    produto = Produto.objects.get(id=id_produto)

    if request.method == "GET":
        if request.user == produto.vendedor:
            return render(request, "editar_produto.html", {"produto": produto})
        else:
            return redirect("home")

    elif request.method == "POST":
        if request.user != produto.vendedor:
            return redirect("home")

        produto.nome = request.POST.get("nome")
        produto.descricao = request.POST.get("descricao")
        produto.preco = request.POST.get("preco")
        produto.quantidade = request.POST.get("quantidade_estoque")
        imagem = request.FILES.get("imagem")

        if imagem:
            caminho_imagem_antiga = ""
            if produto.imagem:
                caminho_imagem_antiga = os.path.join(
                    settings.MEDIA_ROOT, str(produto.imagem)
                )

            fs = FileSystemStorage(
                location="media/uploads/produtos/", base_url="/media/uploads/produtos/"
            )
            filename = fs.save(imagem.name, imagem)

            produto.imagem = "uploads/produtos/" + filename

            if caminho_imagem_antiga and os.path.isfile(caminho_imagem_antiga):
                os.remove(caminho_imagem_antiga)

        produto.save()

        return redirect("perfil_user", username=produto.vendedor.username)

    return redirect("home")


def adicionar_produto(request, username):
    if request.user.is_authenticated:
        perfil = get_object_or_404(Profile, usuario=request.user)
    else:
        return redirect("home")

    if request.method == "GET":
        if perfil.vendedor and request.user.username == username:
            categorias = Categoria.objects.prefetch_related("subcategorias").all()

            contexto = {"categorias": categorias}
            return render(request, "adicionar_produto.html", contexto)
        else:
            return redirect("home")

    elif request.method == "POST":
        subcategoria_id = request.POST.get("subcategoria")

        if not subcategoria_id:
            return redirect("adicionar_produto", username=request.user.username)

        subcategoria_obj = get_object_or_404(Subcategoria, id=subcategoria_id)

        produto = Produto(vendedor=request.user)
        produto.nome = request.POST.get("nome")
        produto.descricao = request.POST.get("descricao")
        produto.preco = request.POST.get("preco")
        produto.quantidade = request.POST.get("quantidade_estoque")

        produto.subcategoria = subcategoria_obj

        imagem = request.FILES.get("imagem")
        if imagem:
            fs = FileSystemStorage(
                location="media/uploads/produtos/", base_url="/media/uploads/produtos/"
            )
            filename = fs.save(imagem.name, imagem)
            produto.imagem = "uploads/produtos/" + filename

        produto.save()

        return redirect("perfil_user", username=request.user.username)


def excluir_produto(request, id_produto):
    produto = get_object_or_404(Produto, id=id_produto)

    if request.method == "POST":

        if produto.imagem:
            imagem_path = produto.imagem.path
            if os.path.exists(imagem_path):
                os.remove(imagem_path)
        produto.delete()
        return redirect("lista_produtos", username=request.user.username)

    return redirect("lista_produtos", username=request.user.username)


def vendas(request):
    orders = request.user.order_seller.all()
    return render(request, "vendas.html", {"orders": orders})


def vendas_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.vendedor != request.user:
        raise Http404

    itemOrders = order.itens.all()
    return render(request, "vendas_details.html", {"itemOrders": itemOrders})


def conectar_mercado_pago(request):
    if not request.user.is_authenticated:
        messages.error(request, "Você precisa estar logado para realizar esta ação.")
        return redirect("logar")

    APP_ID = os.getenv("MP_APP_ID")

    redirect_uri = request.build_absolute_uri(reverse("mp_callback"))

    auth_url = (
        f"https://auth.mercadopago.com.br/authorization"
        f"?client_id={APP_ID}"
        f"&response_type=code"
        f"&platform_id=mp"
        f"&state={request.user.id}"
        f"&redirect_uri={redirect_uri}"
    )

    return redirect(auth_url)


def mercado_pago_callback(request):
    code = request.GET.get("code")
    user_id = request.GET.get("state")

    try:
        user = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError):
        messages.error(request, "Usuário inválido durante a autenticação.")
        return redirect("home")

    if not code:
        messages.error(
            request, "A autorização falhou (código não recebido). Tente novamente."
        )
        return redirect("perfil_user", username=user.username)

    token_url = "https://api.mercadopago.com/oauth/token"
    payload = {
        "client_secret": os.getenv("MP_CLIENT_SECRET"),
        "client_id": os.getenv("MP_APP_ID"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": request.build_absolute_uri(reverse("mp_callback")),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        user.perfil.mp_access_token = data.get("access_token")
        user.perfil.mp_refresh_token = data.get("refresh_token")
        user.perfil.mp_user_id = data.get("user_id")
        user.perfil.mp_connected = True
        user.perfil.save()
        messages.success(request, "Sua conta Mercado Pago foi conectada com sucesso!")
        return redirect("perfil_user", username=user.username)
    else:
        error_message = "Erro desconhecido na resposta do Mercado Pago."
        try:
            error_message = response.json().get("message", error_message)
        except Exception:
            pass
        messages.error(
            request, f"Não foi possível finalizar a conexão: {error_message}"
        )
        return redirect("perfil_user", username=user.username)
