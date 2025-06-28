# test_full_flow.py (සම්පූර්ණ යාවත්කාලීන කළ script එක)

import requests
import json
from wallet import Wallet
import time

BLOCKCHAIN_NODE_URL = "http://127.0.0.1:5000"

def post_transaction(payload):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{BLOCKCHAIN_NODE_URL}/transactions/new", data=json.dumps(payload), headers=headers)
    print(f"POST /transactions/new | Status: {response.status_code}, Response: {response.json()}")
    return response.ok

def mine_block():
    print("\nAttempting to mine a new block...")
    response = requests.get(f"{BLOCKCHAIN_NODE_URL}/mine")
    if response.ok:
        print("✅ Block mined successfully!")
    else:
        print("❌ Mining failed.")
    time.sleep(1) 

def main():
    university_wallet = Wallet()
    student_wallet = Wallet()
    print("--- Wallets Created ---")

    # To simplify, we will just send the VC issuance transaction.
    # In a real system, DIDs should be registered first.
    
    # 1. University issues a Verifiable Credential to the Student
    # The credential data itself
    credential_data = {"type": "BachelorsDegree", "major": "Computer Science", "university": "University of LockCore"}
    # The University signs the credential data
    credential_signature = university_wallet.sign(credential_data)

    # 2. Create the main transaction payload
    issue_vc_transaction = {
        "type": "issue_vc",
        "issuer_address": university_wallet.address, # The address paying the transaction fee
        "issuer_public_key": university_wallet.public_key, # **NEW**: We now include the public key for verification
        "subject_did": f"did:lockcore:{student_wallet.address}",
        "credential_data": credential_data,
        "issuer_signature": credential_signature
    }

    # 3. The University signs the ENTIRE TRANSACTION to authorize it on the blockchain
    final_transaction_signature = university_wallet.sign(issue_vc_transaction)

    # 4. Create the final API payload
    api_payload = {
        "transaction": issue_vc_transaction,
        "signature": final_transaction_signature,
        "public_key": university_wallet.public_key
    }

    # 5. Send the VC issuance transaction to the node
    print("\nIssuing a Verifiable Credential with full verification...")
    post_transaction(api_payload)
    
    # 6. Mine a block to confirm the VC
    mine_block()
    
    # 7. Retrieve and verify the credentials
    print("\n--- Retrieving Credentials for Student ---")
    student_did_string = f"did:lockcore:{student_wallet.address}"
    response = requests.get(f"{BLOCKCHAIN_NODE_URL}/identity/credentials/get/{student_did_string}")
    print(f"GET /identity/credentials/get/... | Status: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=4))

if __name__ == '__main__':
    main()