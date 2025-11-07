from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user import UserCreate, User
from app.crud.user import create_user, get_user_by_id, get_user_by_email, get_users
from app.db.session import get_db

router = APIRouter()

@router.post("/users/", response_model=User)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db=db, user=user)

@router.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_users(db, skip=skip, limit=limit)

@router.get("/users/{id}", response_model=User)
def read_user(id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user