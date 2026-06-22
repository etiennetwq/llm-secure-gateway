from database import get_db_connection


def log_security_alert(
    user_id: int,
    blocked_prompt: str,
    attack_type: str,
    client_ip: str
) -> None:

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO security_alerts
        (
            user_id,
            blocked_prompt,
            attack_type,
            client_ip
        )
        VALUES
        (?, ?, ?, ?)
        """,
        (
            user_id,
            blocked_prompt,
            attack_type,
            client_ip
        )
    )

    conn.commit()
    conn.close()