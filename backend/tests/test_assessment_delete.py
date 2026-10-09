"""
Tests for the DELETE /assessment/{assessment_id} endpoint.

The Assessment table uses PostgreSQL-specific types (JSONB/UUID), so it cannot
be created in the SQLite test database used by test_auth.py. Instead, the DB
session and the auth dependency are overridden with mocks; the tests then
assert the endpoint's existence / ownership / deletion behaviour directly.
"""
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from database.session import get_db
from database.models import User
from main import app
from services.auth import get_current_user_from_cookie

OWNER_ID = uuid.uuid4()
OTHER_ID = uuid.uuid4()
ASSESSMENT_ID = uuid.uuid4()


def make_user(user_id: uuid.UUID) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = user_id
    return user


def make_assessment(owner_id: uuid.UUID) -> MagicMock:
    assessment = MagicMock()
    assessment.id = ASSESSMENT_ID
    assessment.user_id = owner_id
    return assessment


def make_db(first_result) -> MagicMock:
    """A session mock whose query(...).filter(...).first() returns `first_result`."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = first_result
    return db


@pytest.fixture(autouse=True)
def dependency_overrides():
    """Install per-test overrides and always restore the app afterwards."""
    saved = dict(app.dependency_overrides)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


def set_auth(user: MagicMock | None) -> None:
    """Authenticate as `user`, or as nobody (401) when None."""
    if user is None:
        def raise_401():
            raise HTTPException(status_code=401, detail="Not authenticated")

        app.dependency_overrides[get_current_user_from_cookie] = raise_401
    else:
        app.dependency_overrides[get_current_user_from_cookie] = lambda: user


client = TestClient(app)


def test_delete_owner_succeeds():
    """The owner deleting their own assessment gets 204 and the row is removed."""
    assessment = make_assessment(OWNER_ID)
    db = make_db(assessment)
    app.dependency_overrides[get_db] = lambda: db
    set_auth(make_user(OWNER_ID))

    response = client.delete(f"/assessment/{ASSESSMENT_ID}")

    assert response.status_code == 204
    assert response.content == b""
    db.delete.assert_called_once_with(assessment)
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_delete_unknown_id_returns_404():
    """A well-formed but unknown UUID returns 404 and deletes nothing."""
    db = make_db(None)
    app.dependency_overrides[get_db] = lambda: db
    set_auth(make_user(OWNER_ID))

    response = client.delete(f"/assessment/{ASSESSMENT_ID}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_delete_other_users_assessment_returns_403():
    """An assessment owned by a different user cannot be deleted (403)."""
    assessment = make_assessment(OTHER_ID)
    db = make_db(assessment)
    app.dependency_overrides[get_db] = lambda: db
    set_auth(make_user(OWNER_ID))

    response = client.delete(f"/assessment/{ASSESSMENT_ID}")

    assert response.status_code == 403
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_delete_unauthenticated_returns_401():
    """Without a valid session cookie the request is rejected before any DB work."""
    db = make_db(make_assessment(OWNER_ID))
    app.dependency_overrides[get_db] = lambda: db
    set_auth(None)

    response = client.delete(f"/assessment/{ASSESSMENT_ID}")

    assert response.status_code == 401
    db.delete.assert_not_called()


def test_delete_db_error_returns_500_and_rolls_back():
    """A commit failure rolls the transaction back and surfaces a 500."""
    assessment = make_assessment(OWNER_ID)
    db = make_db(assessment)
    db.commit.side_effect = OperationalError("DELETE assessments", None, Exception("down"))
    app.dependency_overrides[get_db] = lambda: db
    set_auth(make_user(OWNER_ID))

    response = client.delete(f"/assessment/{ASSESSMENT_ID}")

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_delete_invalid_uuid_returns_422():
    """A non-UUID path parameter is rejected by FastAPI validation (422)."""
    db = make_db(None)
    app.dependency_overrides[get_db] = lambda: db
    set_auth(make_user(OWNER_ID))

    response = client.delete("/assessment/not-a-uuid")

    assert response.status_code == 422
