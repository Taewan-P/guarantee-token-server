from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from account import DB, models
from account.DataClass import LoginInfo, AccountInfo

account_router = APIRouter()


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
    account_id = account_info.id
    account_pw = account_info.password

    pass


@account_router.post("/login")
def login(login_info: LoginInfo):
    """
    :param login_info: ID and Password in JSON format.
    :return: JSONResponse with Valid JWT
    """
    login_id = login_info.id
    login_pw = login_info.password

    pass
