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


def parse_alert_details(details_text: str | None) -> dict[str, Any]:
    """
    Safely parse the JSON details field from security_alerts.

    Args:
        details_text: JSON string stored in the database.

    Returns:
        Parsed details dictionary. If parsing fails, returns a fallback dictionary.
    """

    if not details_text:
        return {}

    try:
        parsed_details = json.loads(details_text)

        if isinstance(parsed_details, dict):
            return parsed_details

        return {
            "raw": parsed_details
        }

    except json.JSONDecodeError:
        return {
            "raw": details_text
        }


def get_security_alerts(
    user_id: int | None = None,
    attack_type: str | None = None,
    severity: str | None = None,
    action: str | None = None,
    event_type: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> list[dict]:
    """
    Retrieve structured security alerts for admin audit queries.

    Args:
        user_id: Optional user ID filter.
        attack_type: Optional attack type filter.
        severity: Optional severity filter.
        action: Optional security action filter.
        event_type: Optional event type filter.
        limit: Maximum number of alerts to return.
        offset: Number of alerts to skip.

    Returns:
        A list of structured security alert dictionaries.
    """

    query = """
        SELECT
            id,
            user_id,
            blocked_prompt,
            attack_type,
            client_ip,
            event_type,
            severity,
            risk_score,
            action,
            endpoint,
            details,
            timestamp
        FROM security_alerts
    """

    conditions = []
    params: list = []

    if user_id is not None:
        conditions.append("user_id = ?")
        params.append(user_id)

    if attack_type is not None:
        conditions.append("attack_type = ?")
        params.append(attack_type)

    if severity is not None:
        conditions.append("severity = ?")
        params.append(severity)

    if action is not None:
        conditions.append("action = ?")
        params.append(action)

    if event_type is not None:
        conditions.append("event_type = ?")
        params.append(event_type)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

    finally:
        conn.close()

    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "blocked_prompt": row["blocked_prompt"],
            "attack_type": row["attack_type"],
            "client_ip": row["client_ip"],
            "event_type": row["event_type"],
            "severity": row["severity"],
            "risk_score": row["risk_score"],
            "action": row["action"],
            "endpoint": row["endpoint"],
            "details": parse_alert_details(row["details"]),
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]