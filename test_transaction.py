# test_transaction.py

import requests
import json
from wallet import Wallet

# Create wallets for sender and recipient
sender_wallet = Wallet()
recipient_wallet = Wallet()

# The URL of the blockchain node we want to send the transaction to
blockchain_node_url = "http://127.0.0.1:5000"

# Step 1: Create the transaction data
transaction_data = {
    "sender": sender_wallet.address,
    "recipient": recipient_wallet.address,
    "amount": 123
}

# Step 2: Sign the transaction with the sender's private key
signature = sender_wallet.sign(transaction_data)

# Step 3: Create the payload for the API request
api_payload = {
    "transaction": transaction_data,
    "signature": signature,
    "public_key": sender_wallet.public_key
}

# Step 4: Send the transaction to the blockchain node
headers = {'Content-Type': 'application/json'}
response = requests.post(f"{blockchain_node_url}/transactions/new", data=json.dumps(api_payload), headers=headers)

# Print the response from the server
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.json()}")