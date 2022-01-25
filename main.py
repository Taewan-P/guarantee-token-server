import uvicorn
from fastapi import FastAPI

from account.url import account_router
from node.url import node_router
from tokens.url import token_router

app = FastAPI()

app.include_router(account_router, prefix='/account')
app.include_router(node_router, prefix='/node')
app.include_router(token_router, prefix='/tokens')
