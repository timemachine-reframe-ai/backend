from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, UserCreate, UserUpdate


class UserRepository:
    """Data access layer for User entities."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def get_by_login_id(self, login_id: str) -> Optional[User]:
        return self.session.query(User).filter(User.loginId == login_id).first()

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

    def update(self, user_id: int, payload: UserUpdate) -> Optional[User]:
        user = self.get(user_id)
        if user is None:
            return None

        if payload.username is not None:
            user.username = payload.username
        if payload.email is not None:
            user.email = payload.email
        if payload.password:
            user.password_hash = hash_password(payload.password)

        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get(user_id)
        if user is None:
            return False
        self.session.delete(user)
        self.session.commit()
        return True

    def authenticate(self, credentials: LoginRequest) -> Optional[User]:
        user = self.get_by_login_id(credentials.loginId)
        if user is None:
            return None
        if not verify_password(credentials.password, user.password_hash):
            return None
        return user
