from fastapi import Header
from database import get_db_connection
from errors import raise_api_error


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> int:
    """
    Verify API Key.

    Returns:
        user_id
    """

    if x_api_key is None:
        raise_api_error(
            status_code=401,
            error_code="MISSING_API_KEY",
            message="Missing API key."
        )

    api_key = x_api_key.strip()

    if not api_key:
        raise_api_error(
            status_code=401,
            error_code="INVALID_API_KEY",
            message="Invalid API key."
        )

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE api_key_hash = ?
            AND is_active = 1
            """,
            (api_key,)
        )

        user = cursor.fetchone()

    finally:
        conn.close()

    if not user:
        raise_api_error(
            status_code=401,
            error_code="INVALID_API_KEY",
            message="Invalid API key."
        )

    return user["id"]
