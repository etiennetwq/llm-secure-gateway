import sqlite3
from typing import Any, cast

import pytest
from fastapi import HTTPException

import auth


def setup_test_database(tmp_path, monkeypatch):
    """
    Create a temporary SQLite database for auth tests.

    The real project uses database.get_db_connection(),
    but auth.py imported it directly as auth.get_db_connection.
    Therefore, we patch auth.get_db_connection during tests.
    """
    db_path = tmp_path / "test_auth.db"

    def get_test_connection():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    conn = get_test_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            api_key_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO users (id, username, api_key_hash, is_active)
        VALUES (?, ?, ?, ?)
        """,
        (1, "active_user", "test_token_123", 1)
    )

    cursor.execute(
        """
        INSERT INTO users (id, username, api_key_hash, is_active)
        VALUES (?, ?, ?, ?)
        """,
        (2, "inactive_user", "inactive_token_456", 0)
    )

    conn.commit()
    conn.close()

    monkeypatch.setattr(auth, "get_db_connection", get_test_connection)


def assert_error_detail(
    exception: HTTPException,
    expected_error_code: str,
    expected_message: str
) -> None:
    """
    Assert that an HTTPException uses the standardized error format.
    """

    assert isinstance(exception.detail, dict)

    detail = cast(dict[str, Any], exception.detail)

    assert detail["status"] == "error"
    assert detail["error_code"] == expected_error_code
    assert detail["message"] == expected_message
    assert detail["details"] == {}


def test_valid_api_key_returns_user_id(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    user_id = auth.verify_api_key(x_api_key="test_token_123")

    assert user_id == 1


def test_invalid_api_key_returns_401(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_api_key(x_api_key="wrong_token")

    exception = exc_info.value

    assert exception.status_code == 401
    assert_error_detail(
        exception=exception,
        expected_error_code="INVALID_API_KEY",
        expected_message="Invalid API key."
    )


def test_inactive_api_key_returns_401(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_api_key(x_api_key="inactive_token_456")

    exception = exc_info.value

    assert exception.status_code == 401
    assert_error_detail(
        exception=exception,
        expected_error_code="INVALID_API_KEY",
        expected_message="Invalid API key."
    )


def test_empty_api_key_returns_401(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_api_key(x_api_key="")

    exception = exc_info.value

    assert exception.status_code == 401
    assert_error_detail(
        exception=exception,
        expected_error_code="INVALID_API_KEY",
        expected_message="Invalid API key."
    )

def test_missing_api_key_returns_401(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_api_key(x_api_key=None)

    exception = exc_info.value

    assert exception.status_code == 401
    assert_error_detail(
        exception=exception,
        expected_error_code="MISSING_API_KEY",
        expected_message="Missing API key."
    )
    