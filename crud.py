from database import get_db_connection

def log_chat(user_id: int, prompt: str, response: str, tokens_used: int) -> None:
    """
    Persists the sanitized chat logs and LLM responses into the database.

    Args:
        user_id: The ID of the user sending the prompt
        prompt: The content of the user's message
        response: The content of the LLM's reply
        tokens_used: The total number of tokens consumed in this interaction
    """

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (user_id, prompt, response, tokens_used) VALUES (?, ?, ?, ?)",
        (user_id, prompt, response, tokens_used)
    )

    
    conn.commit()
    conn.close()

def get_recent_history(user_id: int, limit: int = 3) -> list:
    """
    Retrieves the most recent conversation logs for a specific user to implement Sliding Window Memory.

    Args:
        user_id: The ID of the target user
        limit: The maximum number of recent records to retrieve

    Returns:
        list:A chronological list of dictionaries containing prompt and response pairs
    """


    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT prompt, response FROM chat_logs WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    )


    rows = cursor.fetchall()
    conn.close()
    
    return [{"prompt": row["prompt"], "response": row["response"]} for row in reversed(rows)]


