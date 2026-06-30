import sqlite3


DATABASE_NAME = "secure_gateway.db"


def add_column_if_missing(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
    column_definition: str
) -> None:
    """
    Add a column to an existing SQLite table only if the column does not exist.

    This is a lightweight migration helper for local development.

    Args:
        cursor: SQLite cursor.
        table_name: Target table name.
        column_name: Column name to add.
        column_definition: SQLite column definition, for example:
            "TEXT DEFAULT 'prompt_blocked'"
            "INTEGER"
    """

    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def init_database() -> None:
    """
    Initialize the local SQLite database schema.

    This function supports both:
    1. Creating a new database from scratch.
    2. Updating an existing local database by adding missing columns.
    """

    # 1. Connect to the local SQLite database
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Enable foreign key checks for this connection
    cursor.execute("PRAGMA foreign_keys = ON")

    print("Initializing the security gateway database schema...")

    try:
        # 2. Create the users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            api_key_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
        """)

        # 3. Create the chat logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
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
        """)

        # 4. Create the security alerts table
        #
        # For a new database, this creates the latest structured alert schema.
        # For an existing database, missing columns are added below by the
        # lightweight migration helper.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            blocked_prompt TEXT,
            attack_type TEXT,
            client_ip TEXT,
            event_type TEXT DEFAULT 'prompt_blocked',
            severity TEXT,
            risk_score INTEGER,
            action TEXT,
            endpoint TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # 5. Lightweight migrations for existing local databases
        #
        # CREATE TABLE IF NOT EXISTS will not update an already existing table.
        # Therefore, these ALTER TABLE checks make sure older local databases
        # can receive the new structured alert fields.
        add_column_if_missing(
            cursor=cursor,
            table_name="users",
            column_name="is_admin",
            column_definition="INTEGER DEFAULT 0"
        )


        add_column_if_missing(
            cursor=cursor,
            table_name="chat_logs",
            column_name="request_status",
            column_definition="TEXT DEFAULT 'success'"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="chat_logs",
            column_name="risk_score",
            column_definition="INTEGER"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="chat_logs",
            column_name="risk_level",
            column_definition="TEXT"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="chat_logs",
            column_name="risk_category",
            column_definition="TEXT"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="chat_logs",
            column_name="risk_action",
            column_definition="TEXT"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="chat_logs",
            column_name="model",
            column_definition="TEXT"
        )

        # Lightweight migrations for older security_alerts tables
        add_column_if_missing(
            cursor=cursor,
            table_name="security_alerts",
            column_name="event_type",
            column_definition="TEXT DEFAULT 'prompt_blocked'"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="security_alerts",
            column_name="severity",
            column_definition="TEXT"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="security_alerts",
            column_name="risk_score",
            column_definition="INTEGER"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="security_alerts",
            column_name="action",
            column_definition="TEXT"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="security_alerts",
            column_name="endpoint",
            column_definition="TEXT"
        )

        add_column_if_missing(
            cursor=cursor,
            table_name="security_alerts",
            column_name="details",
            column_definition="TEXT"
        )

        # 6. Insert a test account into the users table
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO users
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
                (
                    1,
                    "etienne_test",
                    "test_token_123",
                    1,
                    1
                )
            )

            cursor.execute(
                """
                UPDATE users
                SET is_active = 1,
                    is_admin = 1
                WHERE id = ?
                """,
                (1,)
            )

        except sqlite3.IntegrityError:
            pass

        conn.commit()

        print("🎉 Database schema initialized successfully! 'secure_gateway.db' is ready.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()