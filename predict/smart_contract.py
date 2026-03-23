# ethapp/smart_contract.py
from web3 import Web3
import json

# Connect to Ganache or Infura
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))  # update with your node URL

# Load contract
with open('E:/eth_price_prediction/eth_prediction/predict/abi/abi.json') as f:
    abi = json.load(f)

contract_address = "0xA48371A66ea8190b11F2725a4B8A90D65fA90E64"
contract = w3.eth.contract(address=contract_address, abi=abi)

def user_has_paid(user_address):
    """Check payment status from blockchain."""
    return contract.functions.checkHasPaid(user_address).call()
