from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_user_repository
from app.repositories.user_repository import UserRepository
from app.schemas.user import User, UserCreate

router = APIRouter()


@router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
def create_user_endpoint(
    payload: UserCreate,
    repository: UserRepository = Depends(get_user_repository),
):
    if repository.get_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return repository.create(payload)


@router.get("/", response_model=List[User], summary="List users")
def read_users(
    skip: int = 0,
    limit: int = 10,
    repository: UserRepository = Depends(get_user_repository),
):
    return repository.list(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=User,
    summary="Get a single user by id",
)
def read_user(user_id: int, repository: UserRepository = Depends(get_user_repository)):
    user = repository.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
