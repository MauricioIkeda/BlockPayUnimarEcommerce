from web3 import Web3
from django.conf import settings

def transfer_bnb(private_key, from_address, to_address, amount):
    w3 = Web3(Web3.HTTPProvider(settings.BSC_NODE_URL))

    from_address = Web3.to_checksum_address(from_address)
    to_address = Web3.to_checksum_address(to_address)

    nonce = w3.eth.get_transaction_count(from_address)

    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.to_wei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': w3.to_wei('5', 'gwei'),
        'chainId': 56
    }

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return w3.to_hex(tx_hash)