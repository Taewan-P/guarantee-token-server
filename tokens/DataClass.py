from pydantic import BaseModel


class TokenList(BaseModel):
    token_list: list


class TokenWithOwner(BaseModel):
    tid: int
    owner: str


class TokenOnly(BaseModel):
    tid: int
