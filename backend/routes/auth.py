import re
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from database.models import User
from database.session import get_db
from services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user_from_cookie,
    create_cookie,
    clear_cookie,
    generate_token,
    email_service,
)
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


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


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 7:
            raise ValueError("Password must be at least 7 characters")
        return v


class ChangeEmailInitiateRequest(BaseModel):
    new_email: str
    current_password: str

    @field_validator("new_email")
    @classmethod
    def validate_new_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v.strip().lower()


class ResendVerificationRequest(BaseModel):
    email: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v.strip().lower() if v else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _commit_or_rollback(db: Session, log_msg: str) -> None:
    """Commit the session; rollback and raise 500 on failure."""
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"DB commit failed in {log_msg}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again.",
        )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["auth"])


# -- Registration --

@router.post("/register")
def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    verification_token = generate_token()
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        verification_token=verification_token,
        verification_token_expires=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(new_user)
    _commit_or_rollback(db, "register")
    db.refresh(new_user)

    # Auto-login: set the access_token cookie
    access_token = create_access_token(data={"sub": str(new_user.id)})
    create_cookie(response, access_token)

    # Non-blocking email — user gets confirmation either way
    email_ok = email_service.send_verification(new_user.email, verification_token)
    if not email_ok:
        logger.warning("Registration succeeded but verification email not sent to %s", new_user.email)

    logger.info("User %s registered successfully", new_user.id)
    return {"message": "User registered successfully"}


# -- Login --

@router.post("/login")
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        logger.warning("Login failed: no account for %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email address.",
        )
    if not verify_password(user_data.password, user.hashed_password):
        logger.warning("Login failed: wrong password for %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    create_cookie(response, access_token)
    logger.info("User %s logged in successfully", user.id)
    return {"message": "Login successful"}


# -- Logout --

@router.post("/logout")
def logout(response: Response):
    clear_cookie(response)
    return {"message": "Logged out"}


# -- Get current user --

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user_from_cookie)):
    return {
        "email": current_user.email,
        "id": current_user.id,
        "email_verified": current_user.email_verified,
    }


# -- Change Password --

@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if req.current_password == req.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password.",
        )

    current_user.hashed_password = get_password_hash(req.new_password)
    current_user.password_changed_at = datetime.utcnow()
    _commit_or_rollback(db, "change-password")

    logger.info("User %s changed password", current_user.id)
    return {"message": "Password changed successfully."}


# -- Change Email — Initiate --

@router.post("/change-email/initiate")
def change_email_initiate(
    req: ChangeEmailInitiateRequest,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if req.new_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email is the same as current email.",
        )

    existing = db.query(User).filter(User.email == req.new_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already in use.",
        )

    token = generate_token()
    current_user.new_email = req.new_email
    current_user.email_change_token = token
    current_user.email_change_token_expires = datetime.utcnow() + timedelta(hours=1)
    _commit_or_rollback(db, "change-email/initiate")

    email_ok = email_service.send_email_change(req.new_email, token)
    if not email_ok:
        logger.warning("Change-email verification not sent to %s", req.new_email)

    logger.info("User %s initiated email change to %s", current_user.id, req.new_email)
    return {
        "message": f"Verification email sent to {req.new_email}. Please check your inbox to confirm."
    }


# -- Change Email — Confirm --

@router.get("/change-email/confirm")
def change_email_confirm(
    token: str,
    db: Session = Depends(get_db),
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing token.",
        )

    user = (
        db.query(User)
        .filter(User.email_change_token == token)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token.",
        )

    if not user.new_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending email change.",
        )

    if (
        user.email_change_token_expires
        and datetime.utcnow() > user.email_change_token_expires.replace(tzinfo=None)
    ):
        user.email_change_token = None
        user.email_change_token_expires = None
        user.new_email = None
        _commit_or_rollback(db, "change-email/confirm (expired)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expired. Please start the email change process again.",
        )

    # Confirm the change
    user.email = user.new_email
    user.email_verified = True
    user.new_email = None
    user.email_change_token = None
    user.email_change_token_expires = None
    _commit_or_rollback(db, "change-email/confirm")

    logger.info("User %s changed email successfully", user.id)
    return {"message": "Email changed successfully."}


# -- Verify Email — Send verification --

@router.post("/verify/send")
def verify_email_send(
    req: ResendVerificationRequest,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified.",
        )

    token = generate_token()
    current_user.verification_token = token
    current_user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    _commit_or_rollback(db, "verify/send")

    email_ok = email_service.send_verification(current_user.email, token)
    if not email_ok:
        logger.warning("Verification email not sent to %s", current_user.email)

    return {
        "message": f"Verification email sent to {current_user.email}."
    }


# -- Verify Email — Confirm --

@router.get("/verify/confirm")
def verify_email_confirm(
    token: str,
    db: Session = Depends(get_db),
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing token.",
        )

    user = (
        db.query(User)
        .filter(User.verification_token == token)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token.",
        )

    if (
        user.verification_token_expires
        and datetime.utcnow() > user.verification_token_expires.replace(tzinfo=None)
    ):
        user.verification_token = None
        user.verification_token_expires = None
        _commit_or_rollback(db, "verify/confirm (expired)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expired. Please request a new verification email.",
        )

    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    _commit_or_rollback(db, "verify/confirm")

    logger.info("User %s verified email successfully", user.id)
    return {"message": "Email verified successfully."}
