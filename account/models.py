from sqlalchemy import Column, Integer, String

from account.DB import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    nickname = Column(String, nullable=False)

    def jsonify(self):
        result = dict()

        result['id'] = self.id
        result['username'] = self.username
        result['nickname'] = self.nickname

        return result
