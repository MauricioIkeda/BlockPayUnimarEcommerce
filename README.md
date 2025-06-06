# 🛒 Unimar Ecommerce

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Django Version](https://img.shields.io/badge/django-5.2.1-green.svg)](https://www.djangoproject.com/download/)
[![CI/CD Status](https://img.shields.io/badge/CI%2FCD-passing-brightgreen.svg)](#cicd-pipeline) Unimar Ecommerce é um projeto acadêmico desenvolvido por alunos da Universidade de Marília (Unimar) com o objetivo de simular uma plataforma de comércio eletrônico. Nosso diferencial é que os produtos e serviços disponíveis no site são os mesmos vendidos pelos alunos da própria sala de aula!

## 💡 Sobre o Projeto

Este ecommerce foi desenvolvido como parte de um projeto para a disciplina de Engenharia De Software. A ideia inicial proposta pelo professor foi criar uma loja virtual onde os alunos da sala pudessem ser vendedores, oferecendo produtos e serviços que já comercializam presencialmente.

Entre os itens que podem ser encontrados, estão:
* Comidas como paçoca, esfirra, hambúrguer 🍔
* Artigos diversos como narguilé 💨
* Serviços: como ajudar com trabalhos acadêmicos, dar carona, entre outros 🚗📚

Além disso, o projeto está evoluindo para se tornar um marketplace completo, onde qualquer aluno pode se cadastrar como vendedor e gerenciar seus próprios produtos e pedidos. A plataforma integra o Mercado Pago para processamento de pagamentos, permitindo que os vendedores conectem suas contas para receber pagamentos de forma segura, com uma taxa de marketplace.

## 🚀 Funcionalidades Principais

* **Para Usuários Compradores:**
    * Cadastro e login de usuários.
    * Navegação por categorias e subcategorias de produtos.
    * Visualização detalhada de produtos.
    * Adição de produtos ao carrinho de compras.
    * Gerenciamento do carrinho (alterar quantidade, remover itens).
    * Finalização de compra separada por vendedor.
    * Pagamento seguro via Mercado Pago.
    * Acompanhamento do status do pagamento (aprovado, pendente, falha).

* **Para Usuários Vendedores:**
    * Solicitação para se tornar um vendedor (requer aprovação de um administrador).
    * Área exclusiva para gerenciamento de produtos (adicionar, editar, excluir).
    * Conexão com a conta do Mercado Pago para recebimento de pagamentos.
    * Visualização do histórico de vendas e detalhes dos pedidos.
    * O estoque dos produtos é atualizado automaticamente após uma venda aprovada.

* **Para Administradores:**
    * Interface administrativa do Django para gerenciamento completo.
    * Aprovação ou recusa de solicitações para se tornar vendedor.
    * Gerenciamento de categorias, subcategorias, produtos e usuários.

* **Plataforma:**
    * Sistema de marketplace com comissão sobre as vendas (configurado em `Store/views.py` como 10%).
    * Notificações via webhook do Mercado Pago para atualização do status dos pagamentos e do estoque.

## 🧰 Tecnologias Utilizadas

* **Backend:**
    * Python 3.10
    * Django 5.2.1 (Framework Web)
    * Mercado Pago SDK (Integração de Pagamento)
    * SQLite (Banco de Dados padrão)
* **Frontend:**
    * HTML5 & CSS3
    * JavaScript (para interatividade no frontend, como menus dropdown)
* **DevOps & Qualidade:**
    * Git & GitHub (Controle de Versão e Repositório)
    * GitHub Actions (CI/CD)
    * Black (Formatador de Código Python)
    * Bandit (Análise de Segurança Estática para Python)
    * djhtml (Lint para Templates Django)
    * Coverage.py (Cobertura de Testes Python)
* **Variáveis de Ambiente:**
    * `python-dotenv` (Para carregar variáveis de ambiente de um arquivo `.env`)

## 🔧 Instalação e Configuração

Siga os passos abaixo para configurar o ambiente de desenvolvimento:

1.  **Pré-requisitos:**
    * Python 3.10 ou superior
    * Pip (gerenciador de pacotes Python)
    * Git

2.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/mauricioikeda/unimar-ecommerce.git](https://github.com/mauricioikeda/unimar-ecommerce.git)
    cd unimar-ecommerce
    ```

3.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

4.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    As principais dependências incluem: `Django`, `mercadopago`, `pillow`, `python-dotenv`, `black`, `bandit`, `djhtml`, `coverage`.

5.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto (onde `manage.py` está localizado) com as seguintes variáveis. Estes são essenciais para a integração com o Mercado Pago:
    ```env
    # .env
    MP_APP_ID=SEU_APP_ID_DO_MERCADO_PAGO
    MP_CLIENT_SECRET=SEU_CLIENT_SECRET_DO_MERCADO_PAGO
    MP_ACCESS_TOKEN=SEU_ACCESS_TOKEN_DE_TESTE_OU_PRODUCAO_DO_MERCADO_PAGO_DA_PLATAFORMA
    ```
    * `MP_APP_ID` e `MP_CLIENT_SECRET`: Usados para o fluxo de conexão da conta do vendedor do Mercado Pago.
    * `MP_ACCESS_TOKEN`: Access Token da *plataforma* (o seu, como dono do marketplace) para interagir com a API do Mercado Pago para algumas operações, como consultar pagamentos via webhook.
    * **Nota:** Os vendedores conectarão suas próprias contas do Mercado Pago, e seus respectivos `access_token`, `refresh_token`, e `mp_user_id` serão armazenados no modelo `Profile` do usuário.

6.  **Aplique as migrações do banco de dados:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7.  **Crie um superusuário (administrador):**
    ```bash
    python manage.py createsuperuser
    ```
    Siga as instruções para definir nome de usuário, email e senha.

8.  **Execute o servidor de desenvolvimento:**
    ```bash
    python manage.py runserver
    ```
    Acesse o site em `http://127.0.0.1:8000/` e a área administrativa em `http://127.0.0.1:8000/admin/`.

## 🏗️ Estrutura do Banco de Dados

O projeto é dividido em duas aplicações principais: `Store` e `Usuario`.

* **App `Usuario`:**
    * `Profile`: Estende o modelo `User` padrão do Django, adicionando campos como `vendedor` (Booleano), `foto`, `bios` e informações de conexão do Mercado Pago (`mp_connected`, `mp_user_id`, `mp_access_token`, `mp_refresh_token`). Um perfil é criado automaticamente para cada novo usuário através de signals.

* **App `Store`:**
    * `Categoria`: Define as categorias principais dos produtos (ex: "Comidas", "Serviços").
    * `Subcategoria`: Define subcategorias dentro de uma categoria pai (ex: "Hambúrguer" dentro de "Comidas").
    * `Produto`: Contém informações do produto como nome, preço, descrição, quantidade em estoque, imagem, vendedor (usuário) e a qual subcategoria pertence.
    * `Carrinho` e `ItemCarrinho`: Gerenciam os itens que um usuário adiciona ao carrinho.
    * `Order` e `ItemOrder`: Representam os pedidos realizados, vinculando comprador, vendedor, itens, valor total e status do pagamento. O `ItemOrder` armazena o preço do produto no momento da compra.
    * `Solicitacao_Vendedor`: Armazena as solicitações de usuários que desejam se tornar vendedores, incluindo nome completo, CPF e descrição dos produtos/serviços.

## 💳 Integração com Mercado Pago

A plataforma utiliza o Mercado Pago para processamento de pagamentos.

* **Conexão do Vendedor:** Vendedores precisam conectar suas contas do Mercado Pago à plataforma. Isso é feito através de um fluxo OAuth2, onde as credenciais (`mp_access_token`, `mp_refresh_token`, `mp_user_id`) são armazenadas no perfil do vendedor.
* **Processamento de Pagamento:** Ao finalizar uma compra para um determinado vendedor, o sistema gera uma preferência de pagamento utilizando o `access_token` *do vendedor*.
* **Taxa do Marketplace:** Uma taxa de 10% (`MARKETPLACE_FEE_PERCENTAGE`) é configurada para ser descontada do vendedor e repassada para a conta da plataforma durante a transação.
* **Notificações (Webhook):** Um endpoint (`/webhook/mercadopago/`) está configurado para receber notificações do Mercado Pago sobre o status dos pagamentos. Quando um pagamento é aprovado (`approved`), o sistema atualiza o status do pedido e deduz a quantidade vendida do estoque do produto. Outros status (como `pending`) também são atualizados.

## 🔄 CI/CD Pipeline (Automação de Integração e Entrega Contínua)

O projeto utiliza GitHub Actions para automatizar testes e verificações de qualidade a cada `push` ou `pull_request` nas branches `main` e `develop`. O pipeline inclui os seguintes passos:

1.  **Checkout do código:** Baixa a versão mais recente do código.
2.  **Configurar ambiente Python:** Define a versão do Python para 3.10.
3.  **Cache de dependências:** Armazena as dependências para acelerar builds futuras.
4.  **Instalar dependências e ferramentas:** Instala as bibliotecas listadas no `requirements.txt` e ferramentas de desenvolvimento como `black`, `bandit` e `djhtml`.
5.  **Formatar o código com Black:** Verifica se o código está formatado de acordo com os padrões do Black.
6.  **Análise de Segurança Estática com Bandit:** Executa o Bandit para identificar potenciais vulnerabilidades de segurança. O resultado é salvo em `bandit_report.json`.
7.  **Lint de Templates Django com djhtml:** Verifica a formatação dos templates HTML do Django.
8.  **Checar migrations pendentes:** Garante que todas as alterações nos modelos foram refletidas em arquivos de migração.
9.  **Rodar testes com coverage:** Executa os testes unitários e de integração (definidos em `Store/tests.py` e `Usuario/tests.py`) e gera um relatório de cobertura.
10. **Gerar relatório de cobertura em HTML:** Cria um relatório HTML da cobertura dos testes.
11. **Publicar HTML do coverage como artefato:** Disponibiliza o relatório de cobertura HTML como um artefato do build.

## 🎓 Público-Alvo

Atualmente, o sistema é voltado apenas para os alunos da Unimar, criando uma solução prática e digital para facilitar a venda dos produtos que já são ofertados fisicamente na universidade.

## 🤝 Contribuindo

Contribuições são bem-vindas! Se você deseja contribuir para o projeto, por favor, siga os passos:

1.  Faça um Fork do projeto.
2.  Crie uma branch para sua Feature (`git checkout -b feature/MinhaFeature`).
3.  Faça commit de suas mudanças (`git commit -m 'Adicionando MinhaFeature'`).
4.  Faça push para a Branch (`git push origin feature/MinhaFeature`).
5.  Abra um Pull Request.

## 📜 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE.txt](LICENSE.txt) para mais detalhes.

---

Desenvolvido por alunos da Unimar.
