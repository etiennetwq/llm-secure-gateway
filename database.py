import sqlite3

def get_db_connection() -> sqlite3.Connection:
    """
    Establishes and configures the connection to the SQLite database.

    Returns:
        sqlite3.Connection:A connection object with row_factory enabled for dict-like row access
    """

    conn = sqlite3.connect("secure_gateway.db")
    conn.row_factory = sqlite3.Row  
    return conn
