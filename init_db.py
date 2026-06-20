import sqlite3

def init_database():
    # 1. Connect to the local SQLite database (auto-created if it doesn't exist)
    conn = sqlite3.connect("secure_gateway.db")
    cursor = conn.cursor()
    
    print("Initializing the security gateway database schema...")

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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 4. Create the security alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS security_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        blocked_prompt TEXT,
        attack_type TEXT,
        client_ip TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 5. Insert a test account into the users table
    try:
        # Using plaintext temporarily; will upgrade to cryptographic hashes later
        cursor.execute("INSERT OR IGNORE INTO users (id, username, api_key_hash) VALUES (1, 'etienne_test', 'test_token_123')")
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()
    print("🎉 Database schema initialized successfully! 'secure_gateway.db' generated.")

if __name__ == "__main__":
    init_database()