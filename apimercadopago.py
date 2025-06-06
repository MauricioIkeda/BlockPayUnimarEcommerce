# apimercadopago.py
import mercadopago
import os
from dotenv import (
    load_dotenv,
)


def realizar_pagamento(seller_access_token, items, external_reference, fee_amount):
    load_dotenv()

    if not seller_access_token:
        raise Exception("seller_access_token não fornecido para realizar_pagamento.")

    sdk = mercadopago.SDK(seller_access_token)

    preference_data = {
        "items": items,
        "back_urls": {
            "success": "https://unimarprojects.pythonanywhere.com/carrinho/compra_realizada/",
            "failure": "https://unimarprojects.pythonanywhere.com/carrinho/compra_falha/",
            "pending": "https://unimarprojects.pythonanywhere.com/carrinho/compra_pendente/",
        },
        "auto_return": "all",
        "notification_url": "https://unimarprojects.pythonanywhere.com/webhook/mercadopago/",
        "external_reference": external_reference,
        "marketplace_fee": float(fee_amount),
    }

    print(
        "--- DEBUG API MP (Seller Token Model): Enviando Preference Data:",
        preference_data,
    )

    preference_response = sdk.preference().create(preference_data)

    if "response" not in preference_response:
        print(
            "--- DEBUG API MP (Seller Token Model): Erro Completo:", preference_response
        )
        error_details = preference_response.get(
            "message", "Erro desconhecido ao criar preferência."
        )
        raise Exception(f"Erro ao criar link de pagamento: {error_details}")

    if "init_point" in preference_response["response"]:
        print(
            "--- DEBUG API MP (Seller Token Model): Sucesso, init_point:",
            preference_response["response"]["init_point"],
        )
        return preference_response["response"]["init_point"]
    else:
        print(
            "--- DEBUG API MP (Seller Token Model): Erro na Resposta:",
            preference_response["response"],
        )
        error_details = preference_response["response"].get(
            "message", "init_point não encontrado na resposta"
        )
        raise Exception(f"Erro ao criar link de pagamento: {error_details}")
