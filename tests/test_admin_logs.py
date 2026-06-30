import sqlite3
from typing import Any, cast

import pytest
from fastapi import HTTPException

import auth
import crud
import main


def setup_admin_test_database(tmp_path, monkeypatch):
    """
    Create a temporary SQLite database for admin log query tests.
    """

    db_path = tmp_path / "test_admin_logs.db"

    def get_test_connection():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    conn = get_test_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            api_key_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prompt TEXT,
            response TEXT,
            tokens_used INTEGER,
            request_status TEXT DEFAULT 'success',
            risk_score INTEGER,
            risk_level TEXT,
            risk_category TEXT,
            risk_action TEXT,
            model TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    cursor.executemany(
        """
        INSERT INTO users
        (
            id,
            username,
            api_key_hash,
            is_active,
            is_admin
        )
        VALUES
        (?, ?, ?, ?, ?)
        """,
        [
            (1, "admin_user", "admin_token", 1, 1),
            (2, "normal_user", "normal_token", 1, 0),
            (3, "inactive_admin", "inactive_admin_token", 0, 1)
        ]
    )

    cursor.executemany(
        """
        INSERT INTO chat_logs
        (
            user_id,
            prompt,
            response,
            tokens_used,
            request_status,
            risk_score,
            risk_level,
            risk_category,
            risk_action,
            model
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "admin low risk prompt",
                "admin low risk response",
                10,
                "success",
                0,
                "low",
                "normal",
                "allow",
                "deepseek-v4-flash"
            ),
            (
                2,
                "normal medium risk prompt",
                "normal medium risk response",
                20,
                "success",
                50,
                "medium",
                "prompt_injection",
                "warn",
                "deepseek-v4-flash"
            ),
            (
                2,
                "normal low risk prompt",
                "normal low risk response",
                30,
                "success",
                0,
                "low",
                "normal",
                "allow",
                "deepseek-v4-flash"
            )
        ]
    )

    conn.commit()
    conn.close()

    monkeypatch.setattr(auth, "get_db_connection", get_test_connection)
    monkeypatch.setattr(crud, "get_db_connection", get_test_connection)

    return get_test_connection


def assert_error_detail(
    exception: HTTPException,
    expected_status_code: int,
    expected_error_code: str,
    expected_message: str
) -> None:
    """
    Assert standardized HTTPException error detail.
    """

    assert exception.status_code == expected_status_code
    assert isinstance(exception.detail, dict)

    detail = cast(dict[str, Any], exception.detail)

    assert detail["status"] == "error"
    assert detail["error_code"] == expected_error_code
    assert detail["message"] == expected_message
    assert detail["details"] == {}


def test_verify_admin_api_key_allows_admin_user(tmp_path, monkeypatch):
    setup_admin_test_database(tmp_path, monkeypatch)

    admin_user_id = auth.verify_admin_api_key(x_api_key="admin_token")

    assert admin_user_id == 1


def test_verify_admin_api_key_rejects_normal_user(tmp_path, monkeypatch):
    setup_admin_test_database(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_admin_api_key(x_api_key="normal_token")

    exception = exc_info.value

    assert_error_detail(
        exception=exception,
        expected_status_code=403,
        expected_error_code="ADMIN_PERMISSION_REQUIRED",
        expected_message="Admin permission is required."
    )


def test_verify_admin_api_key_rejects_invalid_key(tmp_path, monkeypatch):
    setup_admin_test_database(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_admin_api_key(x_api_key="wrong_token")

    exception = exc_info.value

    assert_error_detail(
        exception=exception,
        expected_status_code=401,
        expected_error_code="INVALID_API_KEY",
        expected_message="Invalid API key."
    )


def test_get_chat_logs_filters_by_user_id_and_risk_level(tmp_path, monkeypatch):
    setup_admin_test_database(tmp_path, monkeypatch)

    logs = crud.get_chat_logs(
        user_id=2,
        risk_level="medium",
        limit=50,
        offset=0
    )

    assert len(logs) == 1
    assert logs[0]["user_id"] == 2
    assert logs[0]["risk_level"] == "medium"
    assert logs[0]["risk_category"] == "prompt_injection"
    assert logs[0]["risk_action"] == "warn"


def test_get_chat_logs_supports_limit_and_offset(tmp_path, monkeypatch):
    setup_admin_test_database(tmp_path, monkeypatch)

    logs = crud.get_chat_logs(
        limit=1,
        offset=1
    )

    assert len(logs) == 1

    # Logs are ordered by id DESC.
    # Inserted IDs are 1, 2, 3.
    # DESC order is 3, 2, 1.
    # limit=1 and offset=1 should return ID 2.
    assert logs[0]["id"] == 2
    assert logs[0]["prompt"] == "normal medium risk prompt"


def test_admin_get_logs_returns_success_response(tmp_path, monkeypatch):
    setup_admin_test_database(tmp_path, monkeypatch)

    response = main.admin_get_logs(
        user_id=None,
        request_status=None,
        risk_level=None,
        risk_category=None,
        limit=2,
        offset=0,
        admin_user_id=1
    )

    assert response["status"] == "success"
    assert response["count"] == 2
    assert response["admin_user_id"] == 1
    assert len(response["logs"]) == 2

    # Logs are ordered by id DESC, so the latest inserted log appears first.
    assert response["logs"][0]["id"] == 3
    assert response["logs"][0]["prompt"] == "normal low risk prompt"

    