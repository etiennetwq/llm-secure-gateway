import time
import os
import asyncio
from collections import defaultdict, deque
from fastapi import HTTPException
from dotenv import load_dotenv


load_dotenv()


# Default configuration
DEFAULT_MAX_REQUESTS = 5
DEFAULT_WINDOW_SECONDS = 60


# Read configuration from environment variables
MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", DEFAULT_MAX_REQUESTS))
WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", DEFAULT_WINDOW_SECONDS))


# In-memory request storage
# Format:
# {
#   user_id: deque([timestamp1, timestamp2, ...])
# }
user_request_logs = defaultdict(deque)


# Lock to avoid race conditions during concurrent requests
rate_limit_lock = asyncio.Lock()


async def check_rate_limit(user_id: int) -> dict:
    """
    Check whether a user has exceeded the rate limit.

    Args:
        user_id: The authenticated user ID.

    Returns:
        dict: Rate limit status information.

    Raises:
        HTTPException: 429 Too Many Requests if the limit is exceeded.
    """

    current_time = time.monotonic()

    async with rate_limit_lock:
        request_times = user_request_logs[user_id]

        # Remove expired request timestamps outside the time window
        while request_times and current_time - request_times[0] > WINDOW_SECONDS:
            request_times.popleft()

        # If the user has already reached the limit, reject the request
        if len(request_times) >= MAX_REQUESTS:
            retry_after = int(WINDOW_SECONDS - (current_time - request_times[0])) + 1

            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Rate limit exceeded",
                    "limit": MAX_REQUESTS,
                    "window_seconds": WINDOW_SECONDS,
                    "retry_after_seconds": retry_after
                },
                headers={
                    "Retry-After": str(retry_after)
                }
            )

        # Record the current request
        request_times.append(current_time)

        remaining_requests = MAX_REQUESTS - len(request_times)

        return {
            "limit": MAX_REQUESTS,
            "window_seconds": WINDOW_SECONDS,
            "remaining_requests": remaining_requests
        }