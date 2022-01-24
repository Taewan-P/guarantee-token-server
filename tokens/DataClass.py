from pydantic import BaseModel


class TokenList(BaseModel):
    token_list: list