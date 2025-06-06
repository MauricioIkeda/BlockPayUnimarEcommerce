from web3 import Web3
import os
from django.conf import settings

class BSCWallet:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BSC_NODE_URL))
    
    def create_temp_wallet(self):
        acct = self.w3.eth.account.create()
        return {
            'address': acct.address,
            'private_key': acct.key.hex()  # Encrypt in production!
        }

def get_usdt_balance(address):
    BSC_RPC = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(BSC_RPC))
    
    # Endereço do contrato da USDT (BEP-20) na BSC
    USDT_CONTRACT = Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955")
    
    # ABI básica para tokens ERC20 (só função balanceOf)
    MIN_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
    ]
    address = Web3.to_checksum_address(address)
    contract = web3.eth.contract(address=USDT_CONTRACT, abi=MIN_ABI)
    balance = contract.functions.balanceOf(address).call()
    return balance / (10 ** 18)  # USDT tem 18 casas na BSC