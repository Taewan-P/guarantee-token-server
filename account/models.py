from sqlalchemy import Column, Integer, String

from account.DB import Base


class User(Base):
    __tablename__ = "User"

    user_id = Column(String, primary_key=True, nullable=False)
    user_pw_encrypted = Column(String, nullable=False)
    user_wallet = Column(String, nullable=False)
    user_type = Column(String, nullable=False)

    def jsonify(self):
        result = dict()

        result['user_id'] = self.user_id
        result['user_id_encrypted'] = self.user_pw_encrypted
        result['user_wallet'] = self.user_wallet
        result['user_type'] = self.user_type

        return result