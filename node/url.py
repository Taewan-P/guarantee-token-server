import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from node.DataClass import Address, Transaction, Approval, Validation

node_router = APIRouter()

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


def not_connected_exception() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={'error': 'Geth node is not connected! Please check the address.'}
    )


def address_invalid_exception() -> JSONResponse:
    return JSONResponse(
        status_code=406,
        content={'error': 'Address parameter is not valid!'}
    )


def node_sync_exception() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={'error': 'Node sync error has occurred. Please try again.'}
    )


def invalid_transfer_exception() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={'error': 'Transfer cannot be made at the moment.'}
    )


def invalid_approval_exception() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={'error', 'Approval not made. Please check if you actually own the token.'}
    )


@node_router.get("/")
async def ping_server() -> JSONResponse:
    if w3.isConnected() is False:
        return not_connected_exception()

    return JSONResponse(
        status_code=200,
        content={'status': 'Geth node is connected.'}
    )


@node_router.post("/mint")
async def mint_token(dest: Address) -> JSONResponse:
    """
    AUTH Needed!
    """
    if w3.isConnected() is False:
        return not_connected_exception()

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        addr = dest.address
        destination = Web3.toChecksumAddress(addr)
    except ValueError:
        return address_invalid_exception()

    tx = contract_instance.functions.safeMint(destination)

    try:
        result = tx.transact({'from': w3.eth.accounts[0]})
    except Exception:
        return invalid_transfer_exception()

    return JSONResponse(
        status_code=200,
        content={'result': 'success', 'txhash': result.hex()}
    )


@node_router.post("/balance")
async def check_balance(account: Address) -> JSONResponse:
    if w3.isConnected() is False:
        return not_connected_exception()

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        address = Web3.toChecksumAddress(account.address)
    except ValueError:
        return address_invalid_exception()

    balance = contract_instance.functions.balanceOf(address)
    try:
        result = balance.call()
    except Exception:
        return node_sync_exception()

    return JSONResponse(
        status_code=200,
        content={'account': address, 'balance': result}
    )


@node_router.post("/tokens")
async def get_token_list(account: Address) -> JSONResponse:
    if w3.isConnected() is False:
        return not_connected_exception()

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        address = Web3.toChecksumAddress(account.address)
    except ValueError:
        return address_invalid_exception()

    balance = contract_instance.functions.balanceOf(address)
    try:
        num_of_tokens = balance.call()
    except Exception:
        return node_sync_exception()

    result = []
    for n in range(num_of_tokens):
        try:
            tid = contract_instance.functions.tokenOfOwnerByIndex(address, n).call()
        except Exception:
            return node_sync_exception()
        else:
            result.append(tid)

    return JSONResponse(
        status_code=200,
        content={'account': address, 'tokens': result}
    )


@node_router.post("/transfer")
async def transfer(body: Transaction) -> JSONResponse:
    if w3.isConnected() is False:
        return not_connected_exception()

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        sender = Web3.toChecksumAddress(body.sender)
        receiver = Web3.toChecksumAddress(body.receiver)
        transactor = Web3.toChecksumAddress(body.transactor)
    except ValueError:
        return address_invalid_exception()

    token_id = body.tid

    try:
        result = contract_instance.functions.safeTransferFrom(sender, receiver, token_id).transact({'from': transactor})
    except Exception as e:
        print(e)
        return invalid_transfer_exception()

    return JSONResponse(
        status_code=200,
        content={'result': 'success', 'txhash': result.hex()}
    )


@node_router.post("/node/approve")
async def approve(body: Approval) -> JSONResponse:
    if w3.isConnected() is False:
        return not_connected_exception()

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)

    try:
        receiver = Web3.toChecksumAddress(body.receiver)
    except ValueError:
        return address_invalid_exception()

    token_id = body.tid

    try:
        result = contract_instance.functions.approve(receiver, token_id).transact({'from': w3.eth.accounts[0]})
    except Exception:
        return invalid_approval_exception()

    return JSONResponse(
        status_code=200,
        content={'result': 'success'}
    )


@node_router.post("/validate")
async def validate_token(body: Validation):
    if w3.isConnected() is False:
        return not_connected_exception()

    token_id = body.tid

    try:
        receiver = Web3.toChecksumAddress(body.owner)
    except ValueError:
        return address_invalid_exception()

    # Validation Process - Validate token by Key-Value tx storage. Key is token id and Value is a stack of account
    # address. Validation will check token id and see if the last element of the stack is the owner. Also,
    # the server will check if the token is from the manufacturer type address.

    # Get value from KV storage using token_id
    tx_history = []

    # Check transaction history and validate token
    if Web3.toChecksumAddress(tx_history[-1]) != receiver:
        return JSONResponse(
            status_code=200,
            content={'result': 'invalid', 'detail': 'Token not properly owned.'}
        )

    # Check the token is from the manufacturer type address

    return JSONResponse(
        status_code=200,
        content={'result': 'valid', 'txHistory': []}
    )
