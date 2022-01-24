import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session


token_router = APIRouter()


@token_router.get("/")
async def ping() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={'result': 'success'}
    )