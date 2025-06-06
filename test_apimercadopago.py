import unittest
from unittest.mock import patch, MagicMock
from apimercadopago import realizar_pagamento


class TestMercadoPago(unittest.TestCase):

    # Cenário 1: Testar o caminho de SUCESSO
    @patch("apimercadopago.mercadopago.SDK")
    def test_realizar_pagamento_sucesso(self, MockSDK):
        """
        Testa se a função retorna o 'init_point' quando a API responde com sucesso.
        """
        mock_sdk_instance = MagicMock()
        mock_preference = MagicMock()
        mock_response_sucesso = {
            "response": {"init_point": "https://www.mercadopago.com.br/pagar"}
        }
        mock_preference.create.return_value = mock_response_sucesso
        mock_sdk_instance.preference.return_value = mock_preference
        MockSDK.return_value = mock_sdk_instance

        seller_token = "TEST-TOKEN"
        items = [
            {"id": "123", "title": "Produto Teste", "quantity": 1, "unit_price": 100}
        ]
        external_reference = "REF-12345"
        application_fee = 10.0

        init_point = realizar_pagamento(
            seller_token, items, external_reference, application_fee
        )

        self.assertEqual(init_point, "https://www.mercadopago.com.br/pagar")
        MockSDK.assert_called_once_with(seller_token)
        mock_preference.create.assert_called_once()

    # Cenário 2: Testar o caminho de FALHA (erro conhecido da API)
    @patch("apimercadopago.mercadopago.SDK")
    def test_realizar_pagamento_falha_api(self, MockSDK):
        """
        Testa se a função levanta uma exceção com a mensagem de erro da API.
        """
        mock_sdk_instance = MagicMock()
        mock_preference = MagicMock()
        mock_response_falha = {"response": {"message": "Invalid seller access token"}}
        mock_preference.create.return_value = mock_response_falha
        mock_sdk_instance.preference.return_value = mock_preference
        MockSDK.return_value = mock_sdk_instance

        with self.assertRaises(Exception) as context:
            realizar_pagamento("TOKEN-INVALIDO", [], "REF-FALHA", 5.0)

        self.assertEqual(
            str(context.exception),
            "Erro ao criar link de pagamento: Invalid seller access token",
        )

    # Cenário 3: Testar o caminho de FALHA (resposta inesperada)
    @patch("apimercadopago.mercadopago.SDK")
    def test_realizar_pagamento_falha_desconhecida(self, MockSDK):
        """
        Testa se a função levanta uma exceção com a mensagem de erro padrão
        quando a resposta da API não tem o formato esperado.
        """
        mock_sdk_instance = MagicMock()
        mock_preference = MagicMock()
        mock_preference.create.return_value = {}
        mock_sdk_instance.preference.return_value = mock_preference
        MockSDK.return_value = mock_sdk_instance

        with self.assertRaises(Exception) as context:
            realizar_pagamento("TOKEN", [], "REF-DESCONHECIDA", 5.0)

        self.assertEqual(
            str(context.exception),
            "Erro ao criar link de pagamento: Erro desconhecido ao criar preferência.",
        )

    # NOVO TESTE ADICIONADO ABAIXO
    # Cenário 4: Testar o caminho de FALHA (token ausente)
    def test_realizar_pagamento_sem_token(self):
        """
        Testa se a função levanta uma exceção quando o seller_access_token não é fornecido.
        """
        # Não precisamos de Mocks aqui, pois a falha ocorre antes de qualquer chamada de API.
        with self.assertRaises(Exception) as context:
            # Chamamos a função com None para o token
            realizar_pagamento(None, [], "REF-SEM-TOKEN", 0)

        # Verificamos a mensagem de erro específica para este caso
        self.assertEqual(
            str(context.exception),
            "seller_access_token não fornecido para realizar_pagamento.",
        )

        # Podemos testar com uma string vazia também para garantir
        with self.assertRaises(Exception) as context:
            realizar_pagamento("", [], "REF-SEM-TOKEN", 0)

        self.assertEqual(
            str(context.exception),
            "seller_access_token não fornecido para realizar_pagamento.",
        )
