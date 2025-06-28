import time
import json
import hashlib
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests
from wallet import Wallet

class Block:
    """Represents a single block in our blockchain."""
    def __init__(self, index, transactions, previous_hash, nonce=0, timestamp=None):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = {
            'index': self.index, 'timestamp': self.timestamp, 'transactions': self.transactions,
            'previous_hash': self.previous_hash, 'nonce': self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    """Manages the entire blockchain."""
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.nodes = set()
        self.mining_reward = 25
        self.difficulty = 4 
        self.genesis_block = self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(index=0, transactions=[], previous_hash="0", nonce=0, timestamp=1751094000)
        self.chain.append(genesis_block)
        return genesis_block

    def new_transaction(self, transaction, signature, public_key):
        tx_type = transaction.get('type')
        if tx_type == 'reward':
            self.pending_transactions.append(transaction)
            return self.last_block.index + 1

        sender_address = hashlib.sha256(public_key.encode()).hexdigest()
        origin_address = transaction.get('sender') or transaction.get('owner_address') or transaction.get('issuer_address')
        
        if not origin_address or origin_address != sender_address: return False
        if not Wallet.verify_signature(public_key, signature, transaction): return False
        
        if tx_type == 'register_did':
            if self.resolve_did(transaction.get('did_string')): return False
        elif tx_type == 'issue_vc':
            if not all([transaction.get(k) for k in ['credential_data', 'issuer_signature', 'issuer_public_key']]): return False
            if not Wallet.verify_signature(transaction['issuer_public_key'], transaction['issuer_signature'], transaction['credential_data']): return False
        elif tx_type != 'transfer': return False

        self.pending_transactions.append(transaction)
        return self.last_block.index + 1

    def mine_new_block(self, miner_address):
        reward_transaction = {'type': 'reward', 'sender': "0", 'recipient': miner_address, 'amount': self.mining_reward}
        transactions_for_block = [reward_transaction] + self.pending_transactions
        new_block_data = {'index': self.last_block.index + 1, 'timestamp': time.time(), 'transactions': transactions_for_block, 'previous_hash': self.last_block.hash}
        nonce = self.proof_of_work(new_block_data)
        block = Block(index=new_block_data['index'], transactions=new_block_data['transactions'], previous_hash=new_block_data['previous_hash'], nonce=nonce, timestamp=new_block_data['timestamp'])
        self.pending_transactions = []
        self.chain.append(block)
        return block
    
    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.get('recipient') == address: balance += tx.get('amount', 0)
                if tx.get('sender') == address: balance -= tx.get('amount', 0)
        return balance
    
    # --- Other methods for consensus, etc. ---
    @property
    def last_block(self): return self.chain[-1]
    def proof_of_work(self, block_data_to_mine):
        nonce = 0
        while True:
            block_data_to_mine['nonce'] = nonce
            hash_result = hashlib.sha256(json.dumps(block_data_to_mine, sort_keys=True).encode()).hexdigest()
            if hash_result.startswith('0' * self.difficulty): return nonce
            nonce += 1
    def resolve_did(self, did_string):
        for block in reversed(self.chain):
            for tx in block.transactions:
                if tx.get('type') == 'register_did' and tx.get('did_string') == did_string: return tx.get('owner_address')
        return None
    def get_vcs_for_did(self, subject_did):
        credentials = [];
        for block in self.chain:
            for tx in block.transactions:
                if tx.get('type') == 'issue_vc' and tx.get('subject_did') == subject_did: credentials.append(tx)
        return credentials
    def register_node(self, address): self.nodes.add(urlparse(address).netloc or urlparse(address).path)
    def valid_chain(self, chain_to_validate):
        if not chain_to_validate or chain_to_validate[0]['hash'] != self.genesis_block.hash: return False
        for i in range(1, len(chain_to_validate)):
            current_block_data = chain_to_validate[i]; previous_block_data = chain_to_validate[i - 1]
            if current_block_data['previous_hash'] != previous_block_data['hash']: return False
            temp_hash = current_block_data.pop('hash')
            if not self.valid_proof(current_block_data, self.difficulty): current_block_data['hash'] = temp_hash; return False
            current_block_data['hash'] = temp_hash
        return True
    def resolve_conflicts(self):
        neighbours = self.nodes; new_chain = None; max_length = len(self.chain)
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']; chain_data = response.json()['chain']
                    if length > max_length and self.valid_chain(chain_data):
                        max_length = length
                        self.chain = [Block(b['index'], b['transactions'], b['previous_hash'], b['nonce'], b['timestamp']) for b in chain_data]
                        return True
            except requests.exceptions.ConnectionError: print(f"Could not connect to node {node}. Skipping.")
        return False

# --- API CODE ---
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # Get the miner's address from a query parameter, or use the node's default ID
    miner_address = request.args.get('miner_address', default=node_identifier, type=str)
    mined_block = blockchain.mine_new_block(miner_address=miner_address)
    response = {'message': "New Block Forged", 'block': mined_block.__dict__}
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction_endpoint():
    values = request.get_json(force=True); required = ['transaction', 'signature', 'public_key']
    if not all(k in values for k in required): return 'Missing values', 400
    success = blockchain.new_transaction(values['transaction'], values['signature'], values['public_key'])
    if success: response = {'message': f'Transaction will be added to Block {blockchain.last_block.index + 1}'}; return jsonify(response), 201
    else: response = {'message': 'Invalid transaction.'}; return jsonify(response), 400

@app.route('/chain', methods=['GET'])
def full_chain(): response = {'chain': [block.__dict__ for block in blockchain.chain], 'length': len(blockchain.chain)}; return jsonify(response), 200
@app.route('/balance/<address>', methods=['GET'])
def get_address_balance(address): response = {'address': address, 'balance': blockchain.get_balance(address)}; return jsonify(response), 200
@app.route('/identity/resolve/<did_string>', methods=['GET'])
def resolve_did_endpoint(did_string):
    owner_address = blockchain.resolve_did(did_string)
    if owner_address: response = {'did': did_string, 'owner_address': owner_address}; return jsonify(response), 200
    else: response = {'message': 'DID not found.'}; return jsonify(response), 404
@app.route('/identity/credentials/get/<subject_did>', methods=['GET'])
def get_credentials_for_did_endpoint(subject_did):
    credentials = blockchain.get_vcs_for_did(subject_did)
    if credentials: response = {'subject_did': subject_did, 'credentials': credentials}; return jsonify(response), 200
    else: response = {'message': 'No credentials found.'}; return jsonify(response), 404
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json(force=True); nodes = values.get('nodes')
    if nodes is None: return "Error: Please supply a valid list of nodes", 400
    for node in nodes: blockchain.register_node(node)
    response = {'message': 'New nodes have been added', 'total_nodes': list(blockchain.nodes)}; return jsonify(response), 201
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced: response = {'message': 'Our chain was replaced', 'new_chain': [b.__dict__ for b in blockchain.chain]}
    else: response = {'message': 'Our chain is authoritative', 'chain': [b.__dict__ for b in blockchain.chain]}
    return jsonify(response), 200

# --- RUN THE APP ---
if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(host='0.0.0.0', port=port)