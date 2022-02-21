import datetime
import os
import random
import string
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from account.DataClass import LoginInfo, AccountInfo
from database import DB, models
from node.url import validate_login_token, invalid_login_token_exception

account_router = APIRouter()

server_address_env = os.environ.get('SERVER_ADDRESS')

if server_address_env is None:
    print('Server Address Environment Variable Missing!!')
    exit(1)

w3 = Web3(HTTPProvider(server_address_env))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


@account_router.post("/create")
async def create_account(account_info: AccountInfo, db: Session = Depends(DB.get_db)) -> JSONResponse:
    """
    :return: JSONResponse with proper status code.
    """
    account_id = account_info.user_id
    account_pw = account_info.password
    account_wallet_pw = account_info.wallet_password

    if db.query(models.User).filter(models.User.user_id == account_id).all():
        return JSONResponse(
            status_code=200,
            content={"error": "Same ID already exists!"}
        )
    else:
        try:
            wallet_address = w3.geth.personal.new_account(account_wallet_pw)
        except:
            return JSONResponse(
                status_code=503,
                content={"error": "Error occured while creating your wallet! Please try again."}
            )
        account_pw_encrypted = bcrypt.hashpw(account_pw.encode('utf-8'), bcrypt.gensalt())

        user = models.User(user_id=account_id, user_pw_encrypted=account_pw_encrypted, user_wallet=wallet_address,
                           user_type="customer")
        db.add(user)
        db.commit()

        return JSONResponse(
            status_code=200,
            content={"account": wallet_address}
        )


@account_router.post("/login")
async def login(login_info: LoginInfo, db: Session = Depends(DB.get_db)) -> JSONResponse:
    """
    :param db: Database session
    :param login_info: ID and Password in JSON format.
    :return: JSONResponse with Valid JWT
    """
    login_id = login_info.user_id
    login_pw = login_info.password

    selected_row = db.query(models.User).filter(models.User.user_id == login_id).first()

    if selected_row:
        user_pw_encrypted = selected_row.user_pw_encrypted
        if bcrypt.checkpw(login_pw.encode('utf-8'), user_pw_encrypted.encode('utf-8')):
            passphrase = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(12))
            encoded_jwt = jwt.encode(
                {
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
                    "uid": login_id
                }, passphrase, algorithm="HS256"
            )
            user = db.query(models.User).filter(models.User.user_id == login_id).first()
            user.passphrase = passphrase
            db.commit()

            return JSONResponse(
                status_code=200,
                content={"jwt": encoded_jwt}
            )
        else:
            return JSONResponse(
                status_code=401,
                content={"error": "Password mismatch!"}
            )
    else:
        return JSONResponse(
            status_code=401,
            content={"error": "ID does not exist!"}
        )


@account_router.get("/get_info")
async def get_user_info(x_access_token: Optional[str] = Header(None), db: Session = Depends(DB.get_db)) -> JSONResponse:
    validity = validate_login_token(x_access_token)

    if validity.get('result', 'invalid') == 'invalid':
        return invalid_login_token_exception()

    extracted = jwt.decode(x_access_token, algorithms='HS256', options={'verify_signature': False,
                                                                        'require': ['exp', 'uid']})

    token_user = db.query(models.User).filter(models.User.user_id == extracted['uid']).first()
    token_user_type = token_user.user_type
    token_wallet = token_user.user_wallet

    return JSONResponse(
        status_code=200,
        content={'uid': extracted['uid'], 'account': token_wallet, 'user_type': token_user_type}
    )
