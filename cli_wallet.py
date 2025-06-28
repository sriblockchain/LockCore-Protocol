# cli_wallet.py
from wallet import Wallet
import requests, json, os

BLOCKCHAIN_NODE_URL = "http://127.0.0.1:5000"

def print_menu():
    print("\n" + "="*30); print("      LockCore CLI Wallet"); print("="*30)
    print("1. Create a new wallet"); print("2. Send LCK"); print("3. Check Balance")
    print("q. Quit"); print("="*30)

def create_new_wallet():
    new_wallet = Wallet(); filename = new_wallet.save_to_file()
    print("\n✅ New wallet created successfully!"); print("="*55)
    print(f"Your new wallet address is: {new_wallet.address}")
    print(f"Your wallet details have been saved to: {filename}")
    print("!!! IMPORTANT: Keep the .pem file safe. This is your private key. !!!"); print("="*55)
    input("\nPress Enter to continue...")

def send_lck():
    print("\n--- Send LCK ---")
    try:
        wallet_file = input("Enter the path to your sender wallet file: ");
        if not os.path.exists(wallet_file): print("❌ ERROR: Wallet file not found."); return
        recipient_address = input("Enter the recipient's address: ")
        amount = float(input("Enter the amount of LCK to send: "))
        sender_wallet = Wallet.load_from_file(wallet_file)
        transaction_data = {"sender": sender_wallet.address, "recipient": recipient_address, "amount": amount}
        signature = sender_wallet.sign(transaction_data)
        api_payload = {"transaction": transaction_data, "signature": signature, "public_key": sender_wallet.public_key}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{BLOCKCHAIN_NODE_URL}/transactions/new", data=json.dumps(api_payload), headers=headers)
        if response.status_code == 201: print("\n✅ SUCCESS: Transaction submitted successfully!")
        else: print(f"\n❌ FAILED: {response.text}")
    except Exception as e: print(f"An unexpected error occurred: {e}")
    input("\nPress Enter to continue...")

# ==============================================================================
# NEW FUNCTION STARTS HERE - අපේ අලුත් ශ්‍රිතය මෙතනින් ආරම්භ වේ
# ==============================================================================
def check_balance():
    """Handles checking the balance of an address."""
    print("\n--- Check Balance ---")
    try:
        address = input("Enter the address to check: ")
        if len(address) == 0:
            print("❌ ERROR: Address cannot be empty.")
            return

        response = requests.get(f"{BLOCKCHAIN_NODE_URL}/balance/{address}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Balance for address {data['address']} is: {data['balance']} LCK")
        else:
            print(f"\n❌ FAILED: Could not retrieve balance. Status: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the blockchain node. Is it running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    input("\nPress Enter to continue...")

def main():
    while True:
        print_menu()
        choice = input("Enter your choice: ")
        if choice == '1': create_new_wallet()
        elif choice == '2': send_lck()
        elif choice == '3': check_balance() # Call the new function
        elif choice.lower() == 'q': print("Exiting wallet. Goodbye!"); break
        else: print("\nInvalid choice. Please try again.")
    
if __name__ == '__main__':
    main()