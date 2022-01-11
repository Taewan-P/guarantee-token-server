import uvicorn
from fastapi import FastAPI

from account.url import account_router
from node.url import node_router

app = FastAPI()

app.include_router(account_router, prefix='/account')
app.include_router(node_router, prefix='/node')


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
