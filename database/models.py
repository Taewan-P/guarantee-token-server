from sqlalchemy import Column, Integer, String, Date
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
    logo = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    production_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    details = Column(String, nullable=False)


class History(Base):
    __tablename__ = "History"

    history_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    token_id = Column(Integer, nullable=False)
    tracking = Column(String, nullable=False)
