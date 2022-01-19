from sqlalchemy import Column, Integer, String, ForeignKey
from database.DB import Base


class User(Base):
    __tablename__ = "User"

    user_id = Column(String, primary_key=True, nullable=False)
    user_pw_encrypted = Column(String, nullable=False)
    passphrase = Column(String)
    user_wallet = Column(String)
    user_type = Column(String, nullable=False)


class Token(Base):
    __tablename__ = "Token"

    token_id = Column(Integer, primary_key=True, nullable=False)


class History(Base):
    __tablename__ = "History"

    history_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token_id = Column(Integer, ForeignKey('Token.token_id'), nullable=False)
    tracking = Column(String, nullable=False)
