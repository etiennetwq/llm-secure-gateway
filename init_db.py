import sqlite3

def init_database():
    # 1. 连接到本地 SQLite 数据库（如果文件不存在，会自动在项目下创建）
    conn = sqlite3.connect("secure_gateway.db")
    cursor = conn.cursor()
    
    print("正在初始化安全网关数据库结构...")

    # 2. 创建用户表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        api_key_hash TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )
    """)

    # 3. 创建对话日志表
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

    # 4. 创建安全拦截告警表
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

    # 5. 顺手往用户表里插入一个测试账号（假设是你自己）
    try:
        # 这里先用明文代替，后面我们会升级成加密哈希
        cursor.execute("INSERT OR IGNORE INTO users (id, username, api_key_hash) VALUES (1, 'etienne_test', 'test_token_123')")
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()
    print("🎉 数据库结构初始化成功！已生成 'secure_gateway.db' 文件。")

if __name__ == "__main__":
    init_database()