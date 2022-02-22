import base64
import datetime
import io
import json
from json import JSONDecodeError
from typing import Optional

import jwt
import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import DB, models
from node.DataClass import Validation
from node.url import validate_login_token, invalid_login_token_exception, validate_token
from tokens.DataClass import TokenList, TokenWithOwner

token_router = APIRouter()


@token_router.get("/")
async def ping() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={'result': 'success'}
    )


@token_router.post("/tokenInfo")
async def load_token_info(body: TokenList, db: Session = Depends(DB.get_db)) -> JSONResponse:
    token_list = body.token_list
    token_infos = list()
    not_founded = list()

    for tokenID in token_list:
        token = db.query(models.Token).filter(models.Token.token_id == tokenID).first()
        if token is not None:
            tokenInfo = {"TokenID": token.token_id,
                         "Logo": token.logo,
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
            encoded_jwt = jwt.encode(
                {
                    "tid": body.tid,
                    "owner": body.owner,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
                },
                key=None, algorithm=None
            )

            qr_code = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
                image_factory=qrcode.image.svg.SvgPathFillImage
            )

            qr_code.add_data(encoded_jwt)
            qr_code.make(fit=True)

            byte_stream = io.BytesIO()
            img = qr_code.make_image()
            img.save(stream=byte_stream)

            base64_converted = base64.b64encode(byte_stream.getvalue())

            return JSONResponse(
                status_code=200,
                content={'result': "data:image/svg+xml;utf8;base64," + base64_converted.decode('utf-8')}
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
