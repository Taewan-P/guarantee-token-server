from pydantic import BaseModel


class NoAuthAddress(BaseModel):
    address: str


class Address(BaseModel):
    address: str
    wallet_password: str


class Transaction(BaseModel):
    sender: str
    receiver: str
    transactor: str
    tid: int


class Approval(BaseModel):
    receiver: str
    tid: int


class Validation(BaseModel):
    tid: int
    owner: str
