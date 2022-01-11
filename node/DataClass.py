from pydantic import BaseModel


class Address(BaseModel):
    address: str


class Transaction(BaseModel):
    sender: str
    receiver: str
    transactor: str
    tid: int


class Approval(BaseModel):
    receiver: str
    tid: int
