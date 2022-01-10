from pydantic import BaseModel


class Address(BaseModel):
    address: str


class Transaction(BaseModel):
    sender: str
    receiver: str
    tid: int
