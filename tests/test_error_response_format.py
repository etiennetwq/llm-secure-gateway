from typing import Any, cast

import pytest
from fastapi import HTTPException

from errors import build_error_detail, raise_api_error


def test_build_error_detail_without_details():
    detail = build_error_detail(
        error_code="TEST_ERROR",
        message="Test error message."
    )

    assert detail == {
        "status": "error",
        "error_code": "TEST_ERROR",
        "message": "Test error message.",
        "details": {}
    }


def test_build_error_detail_with_details():
    detail = build_error_detail(
        error_code="TEST_ERROR",
        message="Test error message.",
        details={
            "field": "prompt",
            "reason": "too_long"
        }
    )

    assert detail == {
        "status": "error",
        "error_code": "TEST_ERROR",
        "message": "Test error message.",
        "details": {
            "field": "prompt",
            "reason": "too_long"
        }
    }


def test_raise_api_error_raises_standardized_http_exception():
    with pytest.raises(HTTPException) as exc_info:
        raise_api_error(
            status_code=403,
            error_code="TEST_FORBIDDEN",
            message="Test forbidden message.",
            details={
                "reason": "blocked"
            },
            headers={
                "X-Test": "true"
            }
        )

    exception = exc_info.value

    assert exception.status_code == 403
    assert exception.headers is not None
    assert exception.headers["X-Test"] == "true"

    assert isinstance(exception.detail, dict)

    detail = cast(dict[str, Any], exception.detail)
    details = cast(dict[str, Any], detail["details"])

    assert detail["status"] == "error"
    assert detail["error_code"] == "TEST_FORBIDDEN"
    assert detail["message"] == "Test forbidden message."
    assert details["reason"] == "blocked"
    