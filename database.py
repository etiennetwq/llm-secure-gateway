import os
import sqlite3
from pathlib import Path


def get_database_path() -> Path:
    """Return the shared SQLite path, overridable for local containers."""

    return Path(os.getenv("DATABASE_PATH", "secure_gateway.db"))


def get_db_connection() -> sqlite3.Connection:
    """
    Establishes and configures the connection to the SQLite database.

    Returns:
        sqlite3.Connection:A connection object with row_factory enabled for dict-like row access
    """

    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row  
    return conn
