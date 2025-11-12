from sqlalchemy import Column, Integer, String
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    loginId = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, index=True, nullable=False)