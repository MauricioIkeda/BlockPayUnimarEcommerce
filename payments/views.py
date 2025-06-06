from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Payment
from .services.bsc import BSCWallet, get_usdt_balance
from .services.qr import generate_moonpay_link, generate_qr_base64
from django.conf import settings
from Core.settings import ADDRESS

class CreatePaymentView(APIView):
    def post(self, request, payment_amount):
        temp_wallet_address = BSCWallet().create_temp_wallet()
        moonpay_link = generate_moonpay_link(ADDRESS, payment_amount)
        qr_code = generate_qr_base64(moonpay_link)

        payment = Payment.objects.create(
            address=temp_wallet_address['address'],
            private_key=temp_wallet_address['private_key'],
            amount_received=payment_amount,
        )

        return Response({
            "payment_id": payment.id,
            "temp_wallet_address": temp_wallet_address['address'],
            "moonpay_link": moonpay_link,
            "qr_code": qr_code,
        })

class CheckPaymentView(APIView):
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"error": "Pagamento não encontrado"}, status=404)

        balance = get_usdt_balance(payment.address)

        return Response({
            "payment_id": payment.id,
            "wallet_address": payment.address,
            "usdt_balance": float(balance),
            "status": payment.status
        })
