import os
import uuid
import secrets
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPException

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database.models import User
from database.session import get_db

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# SMTP config
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@resilienceai.app")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Hashes a plain password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Retrieves the current authenticated user from the HTTP-only cookie.
    Used as a FastAPI dependency via Depends().
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def create_cookie(response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("ENVIRONMENT") == "production",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def clear_cookie(response):
    response.delete_cookie(key="access_token", httponly=True)


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def generate_token() -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(32)


def verify_token(user: User, token_field: str, expires_field: str, token: str) -> bool:
    """
    Generic token-verification helper.
    Checks the token value and expiry against the user's stored fields.
    Returns True if valid (and clears the token), False otherwise.
    """
    stored_token = getattr(user, token_field, None)
    stored_expires = getattr(user, expires_field, None)

    if not stored_token or not stored_expires:
        return False

    if not secrets.compare_digest(stored_token, token):
        return False

    if datetime.utcnow() > stored_expires.replace(tzinfo=None):
        return False

    # Token is valid — clear it to prevent replay
    setattr(user, token_field, None)
    setattr(user, expires_field, None)
    return True


# ---------------------------------------------------------------------------
# Email Service
# ---------------------------------------------------------------------------

class EmailService:
    """Simple SMTP email service. Falls back to console logging in dev."""

    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASS
        self.from_addr = SMTP_FROM
        self._available = bool(self.host and self.user and self.password)

    @property
    def available(self) -> bool:
        return self._available

    def send(self, to: str, subject: str, html: str) -> bool:
        """Send an HTML email. Logs to console if SMTP is not configured."""
        if not self._available:
            logger.info(
                "📧 Email not sent (SMTP not configured). Would have sent:\n"
                f"  To: {to}\n  Subject: {subject}\n  Body preview: {html[:200]}..."
            )
            return False

        msg = MIMEText(html, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to

        try:
            with SMTP(self.host, self.port, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(self.user, self.password)
                smtp.send_message(msg)
            logger.info("Email sent to %s", to)
            return True
        except SMTPException as e:
            logger.error("Failed to send email to %s: %s", to, e)
            return False

    def send_verification(self, to: str, token: str) -> bool:
        """Send email-verification link."""
        link = f"{FRONTEND_URL}/auth/verify?token={token}&type=email_verify"
        html = f"""\
<html><body style="font-family:sans-serif;padding:24px;">
<h2>Verify your email</h2>
<p>Click the link below to verify your email address:</p>
<p><a href="{link}">{link}</a></p>
<p>This link expires in 24 hours.</p>
</body></html>"""
        return self.send(to, "Verify your email — ResilienceAI", html)

    def send_email_change(self, to: str, token: str) -> bool:
        """Send email-change confirmation link."""
        link = f"{FRONTEND_URL}/auth/verify?token={token}&type=email_change"
        html = f"""\
<html><body style="font-family:sans-serif;padding:24px;">
<h2>Confirm your new email</h2>
<p>Click the link below to confirm this email address for your account:</p>
<p><a href="{link}">{link}</a></p>
<p>This link expires in 1 hour.</p>
</body></html>"""
        return self.send(to, "Confirm email change — ResilienceAI", html)


email_service = EmailService()
