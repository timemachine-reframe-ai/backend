from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    """Data access layer for User entities."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> List[User]:
        return self.session.query(User).filter(User.username == username).all()

    def list(self, skip: int = 0, limit: int = 10) -> List[User]:
        return self.session.query(User).offset(skip).limit(limit).all()

    def create(self, payload: UserCreate) -> User:
        hashed_password = hash_password(payload.password)
        db_user = User(
            username=payload.username,
            email=payload.email,
            loginId=payload.loginId,
            password_hash=hashed_password,
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user
