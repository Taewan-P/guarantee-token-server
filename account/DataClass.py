from pydantic import BaseModel


class LoginInfo(BaseModel):
    id: str
    password: str


class AccountInfo(BaseModel):
    id: str
    password: str
