import uvicorn
import json
import os

from fastapi import FastAPI
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from pydantic import BaseModel

truffleFile = json.load(open('./build/contracts/GuaranteeToken.json'))
ABI = truffleFile['abi']

contract_address_env = os.environ.get('CONTRACT_ADDRESS')
server_address_env = os.environ.get('SERVER_ADDRESS')

if contract_address_env is None:
    print('Contract Address Environment Variable Missing!!')
    exit(1)

if server_address_env is None:
    print('Server Address Environment Variable Missing!!')
    exit(1)

CONTRACT_ADDRESS = Web3.toChecksumAddress(contract_address_env)

w3 = Web3(HTTPProvider(server_address_env))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

app = FastAPI()


class Address(BaseModel):
    address: str


@app.get("/")
async def ping_server():
    if w3.isConnected() is False:
        return {'error': 'Geth node is not connected! Please check the address.'}

    return {'status': 'Geth node is connected.'}


@app.post("/mint")
async def mint_token(dest: Address):
    if w3.isConnected() is False:
        return {'error': 'Geth node is not connected! Please check the address.'}

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        addr = dest.address
        destination = Web3.toChecksumAddress(addr)
    except ValueError as e:
        print(f'Destination address not valid! //')
        return {'error': e}

    tx = contract_instance.functions.safeMint(destination)
    result = tx.transact({'from': w3.eth.accounts[0]})
    return {'result': 'success', 'txhash': result.hex()}


@app.post("/balance")
async def check_balance(account: Address):
    if w3.isConnected() is False:
        return {'error': 'Geth node is not connected! Please check the address.'}

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        address = Web3.toChecksumAddress(account.address)
    except ValueError as e:
        print('Address param not valid!')
        return {'error': e}

    balance = contract_instance.functions.balanceOf(address)
    try:
        result = balance.call()
    except Exception as e:
        print('Eth node error!')
        return {'error': e}

    return {'account': address, 'balance': result}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
