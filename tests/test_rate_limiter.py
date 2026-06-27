import asyncio
from typing import Any, cast

import pytest
from fastapi import HTTPException

import rate_limiter


def configure_rate_limiter(monkeypatch, max_requests: int, window_seconds: int) -> None:
    """
    Configure rate limiter settings for each test.

    This avoids depending on real .env values and keeps tests predictable.
    """
    monkeypatch.setattr(rate_limiter, "MAX_REQUESTS", max_requests)
    monkeypatch.setattr(rate_limiter, "WINDOW_SECONDS", window_seconds)

    rate_limiter.user_request_logs.clear()


def test_rate_limiter_allows_requests_under_limit(monkeypatch):
    configure_rate_limiter(
        monkeypatch=monkeypatch,
        max_requests=3,
        window_seconds=60
    )

    async def run_test():
        monkeypatch.setattr(rate_limiter, "rate_limit_lock", asyncio.Lock())

        first_result = await rate_limiter.check_rate_limit(user_id=1)
        second_result = await rate_limiter.check_rate_limit(user_id=1)

        assert first_result["limit"] == 3
        assert first_result["window_seconds"] == 60
        assert first_result["remaining_requests"] == 2

        assert second_result["limit"] == 3
        assert second_result["window_seconds"] == 60
        assert second_result["remaining_requests"] == 1

    asyncio.run(run_test())


def test_rate_limiter_blocks_after_limit_exceeded(monkeypatch):
    configure_rate_limiter(
        monkeypatch=monkeypatch,
        max_requests=2,
        window_seconds=60
    )

    async def run_test():
        monkeypatch.setattr(rate_limiter, "rate_limit_lock", asyncio.Lock())

        await rate_limiter.check_rate_limit(user_id=1)
        await rate_limiter.check_rate_limit(user_id=1)

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(user_id=1)

        exception = exc_info.value

        assert exception.status_code == 429
        assert isinstance(exception.detail, dict)
        assert exception.headers is not None

        detail = cast(dict[str, Any], exception.detail)
        headers = cast(dict[str, str], exception.headers)

        assert detail["message"] == "Rate limit exceeded"
        assert detail["limit"] == 2
        assert detail["window_seconds"] == 60
        assert detail["retry_after_seconds"] > 0
        assert "Retry-After" in headers

    asyncio.run(run_test())


def test_rate_limiter_tracks_users_separately(monkeypatch):
    configure_rate_limiter(
        monkeypatch=monkeypatch,
        max_requests=1,
        window_seconds=60
    )

    async def run_test():
        monkeypatch.setattr(rate_limiter, "rate_limit_lock", asyncio.Lock())

        user_one_result = await rate_limiter.check_rate_limit(user_id=1)
        user_two_result = await rate_limiter.check_rate_limit(user_id=2)

        assert user_one_result["remaining_requests"] == 0
        assert user_two_result["remaining_requests"] == 0

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(user_id=1)

        assert exc_info.value.status_code == 429

    asyncio.run(run_test())


def test_rate_limiter_allows_request_after_window_expires(monkeypatch):
    configure_rate_limiter(
        monkeypatch=monkeypatch,
        max_requests=1,
        window_seconds=1
    )

    async def run_test():
        monkeypatch.setattr(rate_limiter, "rate_limit_lock", asyncio.Lock())

        first_result = await rate_limiter.check_rate_limit(user_id=1)
        assert first_result["remaining_requests"] == 0

        await asyncio.sleep(1.1)

        second_result = await rate_limiter.check_rate_limit(user_id=1)
        assert second_result["remaining_requests"] == 0

    asyncio.run(run_test())