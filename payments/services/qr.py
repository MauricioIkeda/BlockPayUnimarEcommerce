import qrcode
import base64
from io import BytesIO

def generate_qr_base64(url: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    return img_base64


def generate_moonpay_link(wallet_address: str, amount_brl: float = 130.00) -> str:
    base_url = "https://buy.moonpay.com"
    params = f"?walletAddress={wallet_address}&currencyCode=usdt_bsc&baseCurrencyCode=brl&baseCurrencyAmount={amount_brl}"
    url = base_url + params

    return url
