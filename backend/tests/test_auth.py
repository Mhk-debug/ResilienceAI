"""
Tests for the Authentication endpoints.

Uses a temporary SQLite database and TestClient.
Only the User table is created in SQLite (Assessment uses JSONB/UUID
which are PostgreSQL-specific). The dependency override routes all
DB calls to the test engine.

Auth uses HTTP-only cookies, so tests pass cookies between calls.
"""
import pytest
from fastapi.testclient import TestClient
from database.session import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()

from main import app
app.dependency_overrides[get_db] = override_get_db

from database.models import User

@pytest.fixture(autouse=True)
def setup_db():
    """Create only the User table (Assessment uses JSONB/UUID — PG-specific)."""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)

client = TestClient(app, cookies={})


def test_register():
    """A new user can register successfully."""
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"


def test_register_duplicate():
    """Registering the same email twice returns 400."""
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    response = client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_sets_cookie():
    """Login sets an HTTP-only access_token cookie."""
    client.post("/auth/register", json={"email": "login@example.com", "password": "password123"})
    response = client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.cookies


def test_login_wrong_password():
    """Login with wrong password returns 401."""
    client.post("/auth/register", json={"email": "wrongpw@example.com", "password": "password123"})
    response = client.post("/auth/login", json={"email": "wrongpw@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_get_me_authenticated():
    """GET /auth/me returns user data when cookie is present."""
    client.post("/auth/register", json={"email": "me@example.com", "password": "password123"})
    login_resp = client.post("/auth/login", json={"email": "me@example.com", "password": "password123"})

    # Use the cookie from login
    client.cookies = login_resp.cookies
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert "id" in data


def test_get_me_unauthenticated():
    """GET /auth/me without cookie returns 401."""
    client.cookies = {}
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_clears_cookie():
    """Logout clears the access_token cookie."""
    client.post("/auth/register", json={"email": "logout@example.com", "password": "password123"})
    login_resp = client.post("/auth/login", json={"email": "logout@example.com", "password": "password123"})
    client.cookies = login_resp.cookies

    response = client.post("/auth/logout")
    assert response.status_code == 200

    # Cookie should be cleared (value empty or expired)
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    # After logout the cookie value is empty or has max-age=0
    assert "max-age=0" in set_cookie.lower() or "access_token=;" in set_cookie
