# test_identity.py

import requests
import json
from wallet import Wallet

# Create a new wallet that will own the DID
identity_wallet = Wallet()

BLOCKCHAIN_NODE_URL = "http://127.0.0.1:5000"

# Step 1: Create the DID registration transaction data
# The DID format is a standard: did:method:specific-identifier
did_string = f"did:lockcore:{identity_wallet.address}"

did_registration_payload = {
    "type": "register_did",
    "owner_address": identity_wallet.address,
    "did_string": did_string
}

# Step 2: Sign the payload with the wallet's private key
signature = identity_wallet.sign(did_registration_payload)

# Step 3: Create the payload for the API request
api_payload = {
    "transaction": did_registration_payload,
    "signature": signature,
    "public_key": identity_wallet.public_key
}

# Step 4: Send the DID registration transaction to the blockchain node
print(f"Registering DID: {did_string}")
headers = {'Content-Type': 'application/json'}
response = requests.post(f"{BLOCKCHAIN_NODE_URL}/transactions/new", data=json.dumps(api_payload), headers=headers)

# Print the response from the server
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.json()}")