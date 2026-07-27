import re

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import timedelta
from database.models import User
from database.session import get_db
from services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user_from_cookie,
    create_cookie,
    clear_cookie,
)
from pydantic import BaseModel, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class UserCreate(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 7:
            raise ValueError("Password must be at least 7 characters")
        return v

class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 7:
            raise ValueError("Password must be at least 7 characters")
        return v

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Auto-login: set the access_token cookie so the user is authenticated immediately
    access_token = create_access_token(data={"sub": str(new_user.id)})
    create_cookie(response, access_token)
    return {"message": "User registered successfully"}


@router.post("/login")
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="No account found with this email address."
        )
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect password."
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    create_cookie(response, access_token)
    return {"message": "Login successful"}


@router.post("/logout")
def logout(response: Response):
    clear_cookie(response)
    return {"message": "Logged out"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user_from_cookie)):
    return {"email": current_user.email, "id": current_user.id}
