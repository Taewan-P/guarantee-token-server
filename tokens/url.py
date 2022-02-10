from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import DB, models
from tokens.DataClass import TokenList

token_router = APIRouter()


@token_router.get("/")
async def ping() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={'result': 'success'}
    )


@token_router.post("/tokenInfo")
async def load_token_info(body: TokenList, db: Session = Depends(DB.get_db)):
    tokenList = body.token_list
    tokenInfos = list()
    not_founded = list()

    for tokenID in tokenList:
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
            tokenInfos.append(tokenInfo)
        else:
            not_founded.append(tokenID)
    
    return JSONResponse(
        status_code=200,
        content={
            "tokenInfo": tokenInfos,
            "NotFounded": not_founded
        }
    )