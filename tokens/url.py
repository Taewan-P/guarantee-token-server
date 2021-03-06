import base64
import datetime
import io
import json
import os
from json import JSONDecodeError
from typing import Optional

import jwt
import qrcode
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import DB, models
from node.DataClass import Validation
from node.url import validate_login_token, invalid_login_token_exception, validate_token
from tokens.DataClass import TokenList, TokenWithOwner, TokenOnly

token_router = APIRouter()

private_key_env = base64.b64decode(os.environ.get('PRIVATE_KEY'))


@token_router.post("/manufacturer")
async def get_manufacturer_address(body : TokenOnly, db: Session = Depends(DB.get_db)) -> JSONResponse:
    token_id = body.tid
    history = db.query(models.History).filter(models.History.token_id == token_id).first()

    if not history:
        return JSONResponse(
            status_code=200,
            content={'result': 'error', 'detail': 'Mint information does not exist'}
        )

    try:
        minter = db.query(models.User).filter(models.User.user_wallet == history.token_to).first()
    except AttributeError:
        return JSONResponse(
            status_code=503,
            content={'result': 'error', 'detail': 'Unknown server error!'}
        )

    if not minter:
        # This should not happen. If this happens, there is something wrong with History DB and User accounts
        return JSONResponse(
            status_code=404,
            content={'result': 'error', 'detail': 'Account info not found'}
        )

    return JSONResponse(
        status_code=200,
        content={'result': 'success', 'detail': f'{minter.user_wallet}'}
    )


@token_router.post("/tokenInfo")
async def load_token_info(body: TokenList, db: Session = Depends(DB.get_db)) -> JSONResponse:
    token_list = body.token_list
    token_infos = []
    not_founded = []

    for tokenID in token_list:
        token = db.query(models.Token).filter(models.Token.token_id == tokenID).first()
        if token is not None:
            tokenInfo = {"TokenID": token.token_id,
                         "Brand": token.brand,
                         "ProductName": token.product_name,
                         "ProductionDate": token.production_date.strftime("%Y-%m-%d"),
                         "ExpirationDate": token.expiration_date.strftime("%Y-%m-%d"),
                         "Details": token.details
                         }
            token_infos.append(tokenInfo)
        else:
            not_founded.append(tokenID)

    return JSONResponse(
        status_code=200,
        content={
            "tokenInfo": token_infos,
            "NotFounded": not_founded
        }
    )


@token_router.post("/create_qr")
async def create_qr_code(body: TokenWithOwner, db: Session = Depends(DB.get_db),
                         x_access_token: Optional[str] = Header(None)) -> JSONResponse:
    token_validity = validate_login_token(x_access_token)

    if token_validity.get('result', 'invalid') == 'invalid':
        return invalid_login_token_exception()

    result = await validate_token(Validation(tid=body.tid, owner=body.owner), db)

    try:
        if json.loads(result.body.decode('utf-8')).get('result') == 'valid':
            # Successful. Generating QR code.

            payload = {
                    "tid": body.tid,
                    "owner": body.owner,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
            }
            encoded_jwt = jwt.encode(payload, key=private_key_env, algorithm="RS256")

            qr_code = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=6,
                border=4
            )

            qr_code.add_data(encoded_jwt)
            qr_code.make(fit=True)

            byte_stream = io.BytesIO()
            img = qr_code.make_image(fill_color="black", back_color="white")
            img.save(stream=byte_stream, format="PNG")

            base64_converted = base64.b64encode(byte_stream.getvalue())

            return JSONResponse(
                status_code=200,
                content={'result': "data:image/png;base64," + base64_converted.decode('utf-8')}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={'error': 'Invalid request. Do you own the token?'}
            )

    except (UnicodeDecodeError, JSONDecodeError):
        return JSONResponse(
            status_code=503,
            content={'error': 'Error handling token request.'}
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=503,
            content={'error': 'Unknown error. Please try again.'}
        )
