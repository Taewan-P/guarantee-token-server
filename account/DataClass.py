from pydantic import BaseModel


class LoginInfo(BaseModel):
    user_id: str
    password: str


class AccountInfo(BaseModel):
    user_id: str
    password: str
    wallet_password: str
