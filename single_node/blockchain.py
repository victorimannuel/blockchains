import sys
import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask
from flask.globals import request
from flask.json import jsonify

import requests
from urllib.parse import urlparse


class Blockchain(object):
    difficulty_target = "0000"

    def hash_block(self, block):
        block_encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_encoded).hexdigest()

    def __init__(self):
        self.chain = []
        self.current_transaction = []
        # manually create initial transaction
        genesis_hash = self.hash_block("genesis_block")
        self.append_block(
            hash_of_previous_block=genesis_hash,
            nonce=self.proof_of_work(0, genesis_hash, [])
        )

    def proof_of_work(self, index, hash_of_previous_block, transactions):
        nonce = 0
        # bertugas mencari nonce, dengan menambah nonce tiap iterasi
        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):
        # ditampung dahulu lalu di-hash
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()
        content_hash = hashlib.sha256(content).hexdigest()
        return content_hash[:len(self.difficulty_target)] == self.difficulty_target

    def append_block(self, hash_of_previous_block, nonce):
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transaction': self.current_transaction,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }

        # reset current_transaction
        self.current_transaction = []
        self.chain.append(block)
        return block

    def add_transaction(self, sender, recipient, amount):
        self.current_transaction.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        # return self.last_block + 1
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]


# configure Flask
app = Flask(__name__)
# alamat pengirim
node_identifier = str(uuid4()).replace('-', "")
blockchain = Blockchain()

#routes (url/endpoint)
@app.route('/blockchain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/mine', methods=['GET'])
def mine_block():
    blockchain.add_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )

    last_block_hash = blockchain.hash_block(blockchain.last_block)
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transaction)

    block = blockchain.append_block(nonce=nonce, hash_of_previous_block=last_block_hash)
    response = {
        'message': "Block baru telah ditambahkan (mined)",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transaction': block['transaction'],
    }
    return jsonify(response), 200 # sukses

@app.route('/transaction/new', methods=['POST'])
def new_transactions():
    values = request.get_json()

    required_fields = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required_fields):
        return {'Missing fields', 400}

    index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount'],
    )

    response = {
        'message': f"Transaksi akan ditambahkan ke block {index}"
    }
    # 201 karena berhasil ditambahkan (created)
    return jsonify(response), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))
