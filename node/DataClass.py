from pydantic import BaseModel


class NoAuthAddress(BaseModel):
    address: str


class Address(BaseModel):
    address: str
    wallet_password: str
    product_name: str
    prod_date: str
    exp_date: str
    details: str


class Transaction(BaseModel):
    sender: str
    receiver: str
    transactor: str
    tid: int
    wallet_password: str


class Approval(BaseModel):
    receiver: str
    tid: int
    wallet_password: str


class Validation(BaseModel):
    tid: int
    owner: str
