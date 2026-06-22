from fastapi import Header, HTTPException
from database import get_db_connection


def verify_api_key(
    x_api_key: str = Header(...)
) -> int:
    """
    Verify API Key.

    Returns:
        user_id
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE api_key_hash = ?
        AND is_active = 1
        """,
        (x_api_key,)
    )

    user = cursor.fetchone()

    conn.close()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )

    return user["id"]