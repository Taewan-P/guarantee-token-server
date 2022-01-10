import uvicorn
import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from DataClass import Address, Transaction, Approval
from NodeExceptions import *

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


@app.exception_handler(NodeNotConnectedException)
async def not_connected_exception_handler(request: Request):
    return JSONResponse(
        status_code=503,
        content={'error': 'Geth node is not connected! Please check the address.'}
    )


@app.exception_handler(AddressInvalidException)
async def address_invalid_exception_handler(request: Request):
    return JSONResponse(
        status_code=406,
        content={'error': 'Address parameter is not valid!'}
    )


@app.exception_handler(NodeSyncException)
async def node_sync_exception_handler(request: Request):
    return JSONResponse(
        status_code=503,
        content={'error': 'Node sync error has occurred. Please try again.'}
    )


@app.exception_handler(TransferInvalidException)
async def invalid_transfer_exception_handler(request: Request, exception):
    return JSONResponse(
        status_code=503,
        content={'error': 'Transfer cannot be made at the moment.'}
    )


@app.exception_handler(ApprovalInvalidException)
async def invalid_approval_exception_handler(request: Request, exception):
    return JSONResponse(
        status_code=503,
        content={'error', 'Approval not made. Please check if you actually own the token.'}
    )


@app.get("/node")
async def ping_server():
    if w3.isConnected() is False:
        raise NodeNotConnectedException

    return JSONResponse(
        status_code=200,
        content={'status': 'Geth node is connected.'}
    )


@app.post("/node/mint")
async def mint_token(dest: Address):
    if w3.isConnected() is False:
        raise NodeNotConnectedException

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        addr = dest.address
        destination = Web3.toChecksumAddress(addr)
    except ValueError:
        raise AddressInvalidException

    tx = contract_instance.functions.safeMint(destination)

    try:
        result = tx.transact({'from': w3.eth.accounts[0]})
    except Exception:
        raise TransferInvalidException

    return JSONResponse(
        status_code=200,
        content={'result': 'success', 'txhash': result.hex()}
    )


@app.post("/node/balance")
async def check_balance(account: Address):
    if w3.isConnected() is False:
        raise NodeNotConnectedException

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        address = Web3.toChecksumAddress(account.address)
    except ValueError:
        raise AddressInvalidException

    balance = contract_instance.functions.balanceOf(address)
    try:
        result = balance.call()
    except Exception:
        raise NodeSyncException

    return JSONResponse(
        status_code=200,
        content={'account': address, 'balance': result}
    )


@app.post("/node/tokens")
async def get_token_list(account: Address):
    if w3.isConnected() is False:
        raise NodeNotConnectedException

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        address = Web3.toChecksumAddress(account.address)
    except ValueError:
        raise AddressInvalidException

    balance = contract_instance.functions.balanceOf(address)
    try:
        num_of_tokens = balance.call()
    except Exception:
        raise NodeSyncException

    result = []
    for n in range(num_of_tokens):
        try:
            tid = contract_instance.functions.tokenOfOwnerByIndex(address, n).call()
        except Exception:
            raise NodeSyncException
        else:
            result.append(tid)

    return JSONResponse(
        status_code=200,
        content={'account': address, 'tokens': result}
    )


@app.post("/node/transfer")
async def transfer(body: Transaction):
    if w3.isConnected() is False:
        raise NodeNotConnectedException

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        sender = Web3.toChecksumAddress(body.sender)
        receiver = Web3.toChecksumAddress(body.receiver)
        transactor = Web3.toChecksumAddress(body.transactor)
    except ValueError:
        raise AddressInvalidException

    token_id = body.tid

    try:
        result = contract_instance.functions.safeTransferFrom(sender, receiver, token_id).transact({'from': transactor})
    except Exception as e:
        print(e)
        raise TransferInvalidException

    return JSONResponse(
        status_code=200,
        content={'result': 'success', 'txhash': result.hex()}
    )


@app.post("/node/approve")
async def approve(body: Approval):
    if w3.isConnected() is False:
        raise NodeNotConnectedException

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)

    try:
        receiver = Web3.toChecksumAddress(body.receiver)
    except ValueError:
        raise AddressInvalidException

    token_id = body.tid

    try:
        result = contract_instance.functions.approve(receiver, token_id).transact({'from': w3.eth.accounts[0]})
    except Exception:
        raise ApprovalInvalidException

    return JSONResponse(
        status_code=200,
        content={'result': 'success'}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
