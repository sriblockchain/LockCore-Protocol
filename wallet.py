import hashlib
import json
import os
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

class Wallet:
    def __init__(self, private_key_obj=None):
        """
        Initializes a Wallet. If no private key is provided, a new one is generated.
        :param private_key_obj: An ECC key object (optional).
        """
        if private_key_obj:
            self._private_key = private_key_obj
        else:
            # Generate a new private key if one isn't provided
            self._private_key = ECC.generate(curve='P-256')
        
        # Derive the public key from the private key
        self._public_key = self._private_key.public_key()
        self.address = self.generate_address()

    @property
    def private_key(self):
        return self._private_key.export_key(format='PEM')

    @property
    def public_key(self):
        return self._public_key.export_key(format='PEM')
        
    def generate_address(self):
        public_key_pem = self.public_key
        hasher = hashlib.sha256(public_key_pem.encode())
        return hasher.hexdigest()

    def sign(self, data):
        message_string = json.dumps(data, sort_keys=True)
        h = SHA256.new(message_string.encode())
        signer = DSS.new(self._private_key, 'fips-186-3')
        signature = signer.sign(h)
        return signature.hex()
        
    @staticmethod
    def verify_signature(public_key, signature, data):
        try:
            key = ECC.import_key(public_key)
            signature_bytes = bytes.fromhex(signature)
            message_string = json.dumps(data, sort_keys=True)
            h = SHA256.new(message_string.encode())
            verifier = DSS.new(key, 'fips-186-3')
            verifier.verify(h, signature_bytes)
            return True
        except (ValueError, TypeError):
            return False

    # ==============================================================================
    # NEW FUNCTIONS START HERE - අපේ අලුත් ශ්‍රිත මෙතනින් ආරම්භ වේ
    # ==============================================================================
    
    def save_to_file(self, directory="wallets"):
        """
        Saves the private key to a file in PEM format.
        The filename will be based on the wallet address.
        """
        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        filename = f"{directory}/wallet-{self.address}.pem"
        with open(filename, 'wt') as f:
            f.write(self.private_key)
        return filename

    @classmethod
    def load_from_file(cls, filename):
        """
        Loads a wallet by reading a private key from a file.
        :param filename: The path to the wallet file.
        :return: A new Wallet object.
        """
        with open(filename, 'rt') as f:
            private_key_pem = f.read()
        
        private_key_obj = ECC.import_key(private_key_pem)
        # Create a new wallet instance using the loaded key
        return cls(private_key_obj=private_key_obj)


# --- Test Code to check save and load functionality ---
if __name__ == '__main__':
    # 1. Create a new wallet
    wallet1 = Wallet()
    print("--- 1. New Wallet Created ---")
    print(f"Address 1: {wallet1.address}")

    # 2. Save the wallet to a file
    filename = wallet1.save_to_file()
    print(f"\n--- 2. Wallet Saved ---")
    print(f"Wallet 1 saved to file: {filename}")

    # 3. Load the wallet from the file into a new object
    wallet2 = Wallet.load_from_file(filename)
    print(f"\n--- 3. Wallet Loaded ---")
    print(f"Wallet 2 loaded from file: {filename}")
    print(f"Address 2: {wallet2.address}")

    # 4. Verify that both wallets have the same address
    print("\n--- 4. Verification ---")
    if wallet1.address == wallet2.address:
        print("✅ SUCCESS: The saved and loaded wallets are identical.")
    else:
        print("❌ FAILED: The wallets do not match.")