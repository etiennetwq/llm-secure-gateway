import json
from typing import Any

from database import get_db_connection


def log_security_alert(
    user_id: int,
    blocked_prompt: str,
    attack_type: str,
    client_ip: str,
    event_type: str = "prompt_blocked",
    severity: str | None = None,
    risk_score: int | None = None,
    action: str | None = None,
    endpoint: str | None = None,
    details: dict[str, Any] | None = None
) -> None:
    """
    Persist a structured security alert into the database.

    Args:
        user_id: The authenticated user ID.
        blocked_prompt: The prompt blocked by the security scanner.
        attack_type: The detected attack category.
        client_ip: The source client IP address.
        event_type: Structured security event type.
        severity: Risk level such as low, medium, or high.
        risk_score: Numeric risk score from the prompt scanner.
        action: Security action such as block or warn.
        endpoint: API endpoint where the event happened.
        details: Optional JSON-serializable structured metadata.
    """

    details_json = json.dumps(details or {}, ensure_ascii=False)

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO security_alerts
            (
                user_id,
                blocked_prompt,
                attack_type,
                client_ip,
                event_type,
                severity,
                risk_score,
                action,
                endpoint,
                details
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                blocked_prompt,
                attack_type,
                client_ip,
                event_type,
                severity,
                risk_score,
                action,
                endpoint,
                details_json
            )
        )

        conn.commit()

    finally:
        conn.close()