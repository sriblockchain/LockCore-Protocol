# gui_wallet.py

import tkinter as tk
from tkinter import messagebox, filedialog
from wallet import Wallet
import os
import requests
import json

# The URL of a running LockCore node
BLOCKCHAIN_NODE_URL = "http://127.0.0.1:5000"

class WalletApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LockCore GUI Wallet - v1.0")
        self.root.geometry("650x500") # Made the window taller

        self.current_wallet = None

        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # --- Top Frame for Wallet Management ---
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill="x", pady=5)
        
        self.create_wallet_btn = tk.Button(top_frame, text="Create New Wallet", command=self.create_new_wallet)
        self.create_wallet_btn.pack(side="left", padx=5)
        self.load_wallet_btn = tk.Button(top_frame, text="Load Wallet From File", command=self.load_wallet)
        self.load_wallet_btn.pack(side="left", padx=5)
        self.check_balance_btn = tk.Button(top_frame, text="Check Balance", command=self.check_balance)
        self.check_balance_btn.pack(side="left", padx=5)

        # --- Wallet Details Frame ---
        info_frame = tk.LabelFrame(main_frame, text="Wallet Details", padx=10, pady=10)
        info_frame.pack(fill="x", pady=10)
        
        tk.Label(info_frame, text="Address:").grid(row=0, column=0, sticky="w")
        self.address_var = tk.StringVar(root, "No wallet loaded.")
        self.address_entry = tk.Entry(info_frame, textvariable=self.address_var, state="readonly")
        self.address_entry.grid(row=1, column=0, sticky="ew", columnspan=2)

        tk.Label(info_frame, text="Balance:").grid(row=2, column=0, sticky="w", pady=(10,0))
        self.balance_var = tk.StringVar(root, "N/A")
        self.balance_entry = tk.Entry(info_frame, textvariable=self.balance_var, state="readonly", width=30)
        self.balance_entry.grid(row=3, column=0, sticky="w")
        info_frame.grid_columnconfigure(0, weight=1)

        # ==============================================================================
        # SEND LCK FRAME - COMPLETE IMPLEMENTATION
        # ==============================================================================
        send_frame = tk.LabelFrame(main_frame, text="Send LCK", padx=10, pady=10)
        send_frame.pack(fill="both", pady=10, expand=True)

        tk.Label(send_frame, text="Recipient Address:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.recipient_address_var = tk.StringVar(root)
        self.recipient_entry = tk.Entry(send_frame, textvariable=self.recipient_address_var, width=60)
        self.recipient_entry.grid(row=0, column=1, sticky="ew", padx=5)

        tk.Label(send_frame, text="Amount (LCK):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.amount_var = tk.StringVar(root)
        self.amount_entry = tk.Entry(send_frame, textvariable=self.amount_var)
        self.amount_entry.grid(row=1, column=1, sticky="w", padx=5)

        self.send_btn = tk.Button(send_frame, text="Send Transaction", command=self.send_transaction)
        self.send_btn.grid(row=2, column=1, sticky="e", padx=5, pady=10)
        send_frame.grid_columnconfigure(1, weight=1)


    def create_new_wallet(self):
        # ... (no changes here)
        self.current_wallet = Wallet(); saved_file = self.current_wallet.save_to_file()
        self.update_gui_for_wallet(); messagebox.showinfo("Wallet Created", f"New wallet saved to:\n{os.path.abspath(saved_file)}")
    
    def load_wallet(self):
        # ... (no changes here)
        filepath = filedialog.askopenfilename(initialdir=os.path.join(os.getcwd(), "wallets"), title="Select a Wallet File", filetypes=(("PEM files", "*.pem"),("All files", "*.*")))
        if filepath:
            try:
                self.current_wallet = Wallet.load_from_file(filepath); self.update_gui_for_wallet(); messagebox.showinfo("Success", "Wallet loaded!")
            except Exception as e: messagebox.showerror("Error", f"Failed to load wallet.\n\n{e}")

    def update_gui_for_wallet(self):
        # ... (no changes here)
        if self.current_wallet: self.address_var.set(self.current_wallet.address); self.balance_var.set("Click 'Check Balance' to update") 
        else: self.address_var.set("No wallet loaded."); self.balance_var.set("N/A")

    def check_balance(self):
        # ... (no changes here)
        if not self.current_wallet: messagebox.showerror("Error", "Please load a wallet first."); return
        address = self.current_wallet.address
        try:
            response = requests.get(f"{BLOCKCHAIN_NODE_URL}/balance/{address}")
            if response.status_code == 200: self.balance_var.set(f"{response.json().get('balance', 'Error')} LCK")
            else: messagebox.showerror("API Error", f"Could not get balance. Status: {response.status_code}")
        except requests.exceptions.ConnectionError: messagebox.showerror("Connection Error", "Could not connect to the LockCore node.")
        except Exception as e: messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def send_transaction(self):
        """Callback for the 'Send Transaction' button."""
        # 1. Validate inputs
        if not self.current_wallet:
            messagebox.showerror("Error", "Please load your sender wallet first.")
            return
        
        recipient = self.recipient_address_var.get()
        amount_str = self.amount_var.get()
        
        if not recipient or not amount_str:
            messagebox.showerror("Error", "Recipient address and amount cannot be empty.")
            return
            
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Error", "Amount must be a valid number.")
            return

        # 2. Create, sign, and send the transaction
        try:
            transaction_data = {"sender": self.current_wallet.address, "recipient": recipient, "amount": amount, "type": "transfer"}
            signature = self.current_wallet.sign(transaction_data)
            api_payload = {"transaction": transaction_data, "signature": signature, "public_key": self.current_wallet.public_key}
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{BLOCKCHAIN_NODE_URL}/transactions/new", data=json.dumps(api_payload), headers=headers)

            if response.status_code == 201:
                messagebox.showinfo("Success", "Transaction submitted successfully!\n\nIt will be included in the next mined block.")
                self.recipient_address_var.set("")
                self.amount_var.set("")
            else:
                messagebox.showerror("Transaction Failed", f"The node rejected the transaction.\n\nReason: {response.text}")

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", "Could not connect to the LockCore node. Is it running?")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


# --- Main execution block ---
if __name__ == '__main__':
    root = tk.Tk()
    app = WalletApp(root)
    root.mainloop()