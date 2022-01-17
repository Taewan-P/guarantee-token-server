import os

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from account import DB, models
from account.DataClass import LoginInfo, AccountInfo

account_router = APIRouter()

server_address_env = os.environ.get('SERVER_ADDRESS')

if server_address_env is None:
    print('Server Address Environment Variable Missing!!')
    exit(1)

w3 = Web3(HTTPProvider(server_address_env))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


@account_router.get("/{user_id}")
def get_place(user_id: int, db: Session = Depends(DB.get_db)):
    result = db.query(models.User).filter(models.User.id == user_id).first()

    if result is None:
        return JSONResponse(status_code=404, content={"error": 'No account available here.'})

    return JSONResponse(
        status_code=200,
        content={"status": "OK", "data": result.jsonify()}
    )


@account_router.post("/create")
def create_account(account_info: AccountInfo):
    """
    TODO: Create account based on POST body values.
    :return: JSONResponse with proper status code.
    """
    account_id = account_info.user_id
    account_pw = account_info.password
    account_wallet_pw = account_info.wallet_password

    wallet_address = w3.geth.personal.new_account(account_wallet_pw)

    return JSONResponse(
        status_code=200,
        content={'account': wallet_address}
    )


@account_router.post("/login")
def login(login_info: LoginInfo):
    """
    :param login_info: ID and Password in JSON format.
    :return: JSONResponse with Valid JWT
    """
    login_id = login_info.user_id
    login_pw = login_info.password

    pass
