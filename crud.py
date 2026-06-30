from database import get_db_connection


def log_chat(
    user_id: int,
    prompt: str,
    response: str,
    tokens_used: int,
    request_status: str = "success",
    risk_score: int | None = None,
    risk_level: str | None = None,
    risk_category: str | None = None,
    risk_action: str | None = None,
    model: str | None = None
) -> None:
    """
    Persist successful chat logs and related audit metadata into the database.

    Args:
        user_id: The ID of the user sending the prompt.
        prompt: The content of the user's message.
        response: The content of the LLM's reply.
        tokens_used: The total number of tokens consumed in this interaction.
        request_status: Request status, for example "success".
        risk_score: Numeric risk score from the prompt scanner.
        risk_level: Risk level such as low, medium, or high.
        risk_category: Risk category such as normal or prompt_injection.
        risk_action: Scanner action such as allow, warn, or block.
        model: The LLM model used for the request.
    """

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chat_logs
            (
                user_id,
                prompt,
                response,
                tokens_used,
                request_status,
                risk_score,
                risk_level,
                risk_category,
                risk_action,
                model
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                prompt,
                response,
                tokens_used,
                request_status,
                risk_score,
                risk_level,
                risk_category,
                risk_action,
                model
            )
        )

        conn.commit()

    finally:
        conn.close()


def get_recent_history(user_id: int, limit: int = 3) -> list:
    """
    Retrieve the most recent conversation logs for a specific user.

    Args:
        user_id: The ID of the target user.
        limit: The maximum number of recent records to retrieve.

    Returns:
        A chronological list of dictionaries containing prompt and response pairs.
    """

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT prompt, response
            FROM chat_logs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit)
        )

        rows = cursor.fetchall()

    finally:
        conn.close()

    return [
        {
            "prompt": row["prompt"],
            "response": row["response"]
        }
        for row in reversed(rows)
    ]