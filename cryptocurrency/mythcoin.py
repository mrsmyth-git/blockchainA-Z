# Module 2 - Creating a Cryptocurrency

# To be installed
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://getpostman.com/

# Importing Key libs
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

####################################
# Part 1 | Building the Blockchain #
####################################

class Blockchain:

    # Function that runs when an object is created 
    # Initializes the chain and creates the Genisis Block
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()

    
    # Function that creates blocks and appends the blocks created to the chain
    # Returns the block created
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = ''
        self.chain.append(block)
        return block
        
    # Gets the most recent block on the chain
    def get_previous_block(self):
        return self.chain[-1]

    # Checks if the hash of the block starts with '0000'
    # If it doesn't / iterate the new_proof variable and check again 
    # If it does return the new_proof variable
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()     
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    # Encodes the json block
    # Runs the encoded block through the sha256 algo to get the block hash
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    # Checks if chain is valid by:
    # Checking previous block's hash against current blocks previous hash key
    # If it does not match returns False
    # If it does match returns True
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index] 
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()     
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    # Add Transaction
    def add_transaction(self, sender, reciever, amount):
        self.transactions.append({'sender': sender,
                                  'reciever': reciever,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    # Add Node
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    # Replacing the chain with the longest chain if it isnt the longest chain
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain)
                max_length = length
                longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

##################################
# Part 2 | Mining the Blockchain #
##################################

# Creating Web App
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Creating an address for the node on port 5000
node_address = str(uuid()).replace('-', '')

# Creating an instance of a Blockchain
blockchain = Blockchain()

# Mining a new block | Response to a GET http request
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, reciever = 'Kenneth', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'poof': block['proof'],
                'previous_hash': block ['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain | Response to a GET http request
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Getting the validity check of the blockchain | Response to a GET http request
@app.route('/get_validity_check', methods=['GET'])
def get_validity_check():
    response = {'chain': blockchain.chain,
                'validity_check': blockchain.is_chain_valid(blockchain.chain)}
    return jsonify(response), 200

# Adding new transaction to the blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'reciever', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json['sender'], json['reciever'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

#####################################
# 3 | Decentralizing our Blockchain #
#####################################

# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No Node", 401
    for nodes in nodes:
        blockchain.add_node(node)
    response = {'message': 'All nodes have been connected. The MythCoin blockchain now contains the following nodes:' ,
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The chain has been replaced with a more up to date chain',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'The chain has remained the same and is up to date',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200




# Running the app
app.run(host = '0.0.0.0', port = 5000)


