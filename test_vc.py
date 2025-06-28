# test_vc.py

import requests
import json
from wallet import Wallet

# Let's imagine a University (the Issuer) and a Student (the Subject)
university_wallet = Wallet()
student_wallet = Wallet()

BLOCKCHAIN_NODE_URL = "http://127.0.0.1:5000"

# --- For this test to work, the Issuer's DID must already be on the blockchain. ---
# --- We will simulate this in a later, more advanced test. ---
# --- For now, we assume the DIDs exist. ---

# Step 1: Define the Verifiable Credential data
credential_data = {
    "type": "BachelorsDegreeCredential",
    "degree": "BSc in Computer Science",
    "grant_date": "2025-05-20"
}

# The University signs the CREDENTIAL DATA itself to prove its authenticity
credential_signature = university_wallet.sign(credential_data)

# Step 2: Create the main transaction payload to issue the VC
issue_vc_transaction = {
    "type": "issue_vc",
    "issuer_did_owner": university_wallet.address, # The address paying the transaction fee
    "subject_did": f"did:lockcore:{student_wallet.address}",
    "credential_data": credential_data,
    "issuer_signature": credential_signature
}

# Step 3: The University signs the ENTIRE TRANSACTION to authorize it on the blockchain
final_transaction_signature = university_wallet.sign(issue_vc_transaction)

# Step 4: Create the final API payload
api_payload = {
    "transaction": issue_vc_transaction,
    "signature": final_transaction_signature,
    "public_key": university_wallet.public_key
}

# Step 5: Send the VC issuance transaction to the node
print("Issuing a Verifiable Credential...")
headers = {'Content-Type': 'application/json'}
response = requests.post(f"{BLOCKCHAIN_NODE_URL}/transactions/new", data=json.dumps(api_payload), headers=headers)

# Print the response
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.json()}")