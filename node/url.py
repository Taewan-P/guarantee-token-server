import datetime
import json
import os
import jwt

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from database import DB, models
from node.DataClass import NoAuthAddress, Address, Transaction, Approval, Validation

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
        content={'error': 'Approval not made. Please check if you actually own the token.'}
    )


def invalid_login_token_exception() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={'error': 'Login token is not valid.'}
    )


def invalid_permission_exception() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={'error': 'Not authorized (Permission)'}
    )


def wallet_password_mismatch_exception() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={'error': 'Incorrect wallet password'}
    )


def user_doesnt_own_wallet_exception() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={'error': 'User does not own this wallet.'}
    )


def validate_login_token(token: str) -> dict:
    db = next(DB.get_db())
    try:
        extracted = jwt.decode(token, algorithms='HS256', options={'verify_signature': False,
                                                                   'require': ['exp', 'uid']})
    except jwt.exceptions.MissingRequiredClaimError:
        print('Token MissingRequiredClaimError')
        return {'result': 'invalid'}
    except jwt.exceptions.DecodeError:
        print('Token DecodeError')
        return {'result': 'invalid'}

    try:
        passphrase = db.query(models.User).filter(models.User.user_id == extracted['uid']).first().passphrase
        validated = jwt.decode(token, algorithms='HS256', key=passphrase, options={'verify_signature': True,
                                                                                   'require': ['exp', 'uid']})

        if validated != extracted:
            raise jwt.exceptions.InvalidSignatureError

    except jwt.exceptions.InvalidSignatureError:
        print('Token InvalidSignatureError')
        return {'result': 'invalid'}

    current_time = datetime.datetime.now().timestamp()

    if int(validated['exp']) - current_time < 0:
        print('Token ExpiredError')
        return {'result': 'invalid'}

    return {'result': 'valid', 'token': validated}


@node_router.get("/")
async def ping_server(x_access_token: Optional[str] = Header(None)) -> JSONResponse:
    if w3.isConnected() is False:
        return not_connected_exception()

    if not x_access_token:
        return JSONResponse(
            status_code=200,
            content={'status': 'Geth node is connected.'}
        )

    result = validate_login_token(x_access_token)
    if result.get('result', 'invalid') == 'invalid':
        return JSONResponse(
            status_code=200,
            content={'status': 'Geth node is connected.', 'token_status': 'invalid'}
        )
    else:
        return JSONResponse(
            status_code=200,
            content={'status': 'Geth node is connected.', 'token_status': 'valid'}
        )


@node_router.post("/mint")
async def mint_token(dest: Address, db: Session = Depends(DB.get_db),
                     x_access_token: Optional[str] = Header(None)) -> JSONResponse:

    if w3.isConnected() is False:
        return not_connected_exception()

    # Check login token validity
    token_validity = validate_login_token(x_access_token)

    if token_validity.get('result', 'invalid') == 'invalid':
        return invalid_login_token_exception()

    # Check destination address
    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        addr = dest.address
        destination = Web3.toChecksumAddress(addr)
    except ValueError:
        return address_invalid_exception()

    # Check if user owns the wallet
    wallet_user_id = db.query(models.User).filter(models.User.user_wallet == destination).first().user_id
    if wallet_user_id != token_validity['token']['uid']:
        return user_doesnt_own_wallet_exception()

    # Check account type
    minter_type = db.query(models.User).filter(models.User.user_wallet == destination).first().user_type
    if minter_type != "manufacturer":
        return invalid_permission_exception()

    # Unlock wallet
    try:
        account_unlock = w3.geth.personal.unlock_account(destination, dest.wallet_password)
    except ValueError:
        return wallet_password_mismatch_exception()
    else:
        if account_unlock is False:
            return wallet_password_mismatch_exception()
        else:
            print('Account unlock successful')

    tx = contract_instance.functions.safeMint(destination)

    try:
        result = tx.transact({'from': destination})
    except Exception:
        return invalid_transfer_exception()

    # Add transaction history to K-V DB
    tx_info = w3.eth.get_transaction(result.hex())
    minter = tx_info['from']

    # Get token id
    try:
        n_tokens = contract_instance.functions.balanceOf(destination).call()
        token_id = contract_instance.functions.tokenOfOwnerByIndex(destination, n_tokens - 1).call()
        print(f'token_id: {token_id}')
    except Exception as e:
        print(f'Error: {e}')
        return node_sync_exception()

    history = models.History(token_id=token_id, tracking=minter)
    db.add(history)
    db.commit()

    return JSONResponse(
        status_code=200,
        content={'result': 'success', 'txhash': result.hex()}
    )


@node_router.post("/balance")
async def check_balance(account: NoAuthAddress, db: Session = Depends(DB.get_db),
                        x_access_token: Optional[str] = Header(None)) -> JSONResponse:
    if w3.isConnected() is False:
        return not_connected_exception()

    # Check login token validity
    token_validity = validate_login_token(x_access_token)

    if token_validity.get('result', 'invalid') == 'invalid':
        return invalid_login_token_exception()

    contract_instance = w3.eth.contract(abi=ABI, address=CONTRACT_ADDRESS)
    try:
        address = Web3.toChecksumAddress(account.address)
    except ValueError:
        return address_invalid_exception()

    # Check if user owns the wallet
    wallet_user_id = db.query(models.User).filter(models.User.user_wallet == address).first().user_id
    if wallet_user_id != token_validity['token']['uid']:
        return user_doesnt_own_wallet_exception()

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
async def transfer(body: Transaction, db: Session = Depends(DB.get_db)) -> JSONResponse:
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

    # Add result to K-V DB
    tx_info = w3.eth.get_transaction(result.hex())
    receiver_from_tx = tx_info['to']  # Append to K-V DB

    history = models.History(token_id=token_id, tracking=receiver_from_tx)
    db.add(history)
    db.commit()

    return JSONResponse(
        status_code=200,
        content={'result': 'success', 'txhash': result.hex()}
    )


@node_router.post("/approve")
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
async def validate_token(body: Validation, db: Session = Depends(DB.get_db)):
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
    tx_history = list()
    histories = db.query(models.History).filter(models.History.token_id == token_id).all()
    for history in histories:
        tx_history.append(history.tracking)

    # Check transaction history and validate token
    if Web3.toChecksumAddress(tx_history[-1]) != receiver:
        return JSONResponse(
            status_code=200,
            content={'result': 'invalid', 'detail': 'Token not properly owned.'}
        )

    # Check the token is from the manufacturer type address
    minter_type = db.query(models.User).filter(models.User.user_wallet == tx_history[0]).first().user_type
    if minter_type != "manufacturer":
        return JSONResponse(
            status_code=200,
            content={'result': 'invalid', 'detail': 'Token minter is not manufacturer'}
        )

    return JSONResponse(
        status_code=200,
        content={'result': 'valid', 'txHistory': []}
    )
