"""The API and initializer must use the same configurable SQLite path."""

import sqlite3

import database
import init_db


def test_database_connection_uses_configured_path(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "configured.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    init_db.init_database()
    connection = database.get_db_connection()
    try:
        assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert database_path.is_file()
    finally:
        connection.close()
