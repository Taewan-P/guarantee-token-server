from sqlalchemy import Column, Integer, String
from database.DB import Base


class User(Base):
    __tablename__ = "User"

    user_id = Column(String, primary_key=True, nullable=False)
    user_pw_encrypted = Column(String, nullable=False)
    passphrase = Column(String)
    user_wallet = Column(String)
    user_type = Column(String, nullable=False)
