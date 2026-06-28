from typing import Any, NoReturn

from fastapi import HTTPException


def build_error_detail(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Build a standardized API error response body.

    Args:
        error_code: Machine-readable error code.
        message: Human-readable error message.
        details: Optional structured details for debugging or client handling.

    Returns:
        A standardized error detail dictionary.
    """

    return {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "details": details or {}
    }


def raise_api_error(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None
) -> NoReturn:
    """
    Raise a FastAPI HTTPException with standardized error detail.

    Args:
        status_code: HTTP status code.
        error_code: Machine-readable error code.
        message: Human-readable error message.
        details: Optional structured details.
        headers: Optional HTTP headers.
    """

    raise HTTPException(
        status_code=status_code,
        detail=build_error_detail(
            error_code=error_code,
            message=message,
            details=details
        ),
        headers=headers
    )
