from fastapi import FastAPI, Depends, Request, Query
from pydantic import BaseModel, Field
import os
import httpx
from dotenv import load_dotenv

from crud import get_chat_logs, log_chat, get_recent_history
from auth import verify_admin_api_key, verify_api_key
from prompt_scanner import analyze_prompt
from security_alerts import log_security_alert, get_security_alerts
from rate_limiter import check_rate_limit
from errors import raise_api_error

load_dotenv(override=True)

app = FastAPI(
    title="LLM Security Audit Gateway",
    version="2.1"
)


class ChatRequest(BaseModel):
    """
    Represents the incoming payload for a chat interaction.

    Attributes:
        user_id: Must be a valid positive integer.
        prompt: User input with strict length control.
    """

    user_id: int = Field(
        ...,
        gt=0,
        description="Must be a valid positive integer"
    )

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Prompt length strictly limited to 1-200 characters"
    )


@app.get("/health")
def health_check() -> dict:
    """
    Simple health check endpoint.
    """

    return {
        "status": "ok",
        "service": "LLM Security Audit Gateway"
    }

@app.get("/admin/logs")
def admin_get_logs(
    user_id: int | None = Query(default=None, gt=0),
    request_status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    risk_category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin_user_id: int = Depends(verify_admin_api_key)
) -> dict:
    """
    Admin-only endpoint for querying structured chat logs.
    """

    logs = get_chat_logs(
        user_id=user_id,
        request_status=request_status,
        risk_level=risk_level,
        risk_category=risk_category,
        limit=limit,
        offset=offset
    )

    return {
        "status": "success",
        "count": len(logs),
        "admin_user_id": admin_user_id,
        "logs": logs
    }

@app.get("/admin/alerts")
def admin_get_alerts(
    user_id: int | None = Query(default=None, gt=0),
    attack_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    action: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin_user_id: int = Depends(verify_admin_api_key)
) -> dict:
    """
    Admin-only endpoint for querying structured security alerts.
    """

    alerts = get_security_alerts(
        user_id=user_id,
        attack_type=attack_type,
        severity=severity,
        action=action,
        event_type=event_type,
        limit=limit,
        offset=offset
    )

    return {
        "status": "success",
        "count": len(alerts),
        "admin_user_id": admin_user_id,
        "alerts": alerts
    }



@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    http_request: Request,
    authenticated_user_id: int = Depends(verify_api_key)
) -> dict:
    """
    Processes incoming chat requests.

    Workflow:
    1. Verify API key
    2. Apply rate limiting
    3. Analyze prompt risk
    4. Block risky prompts and log security alerts
    5. Retrieve recent conversation history
    6. Call external LLM API asynchronously with httpx
    7. Save successful chat logs
    8. Return LLM response
    """

    # Optional security check:
    # Prevent users from using a valid API key but submitting another user's user_id.
    if request.user_id != authenticated_user_id:
        raise_api_error(
            status_code=403,
            error_code="USER_ID_MISMATCH",
            message="The request user_id does not match the authenticated API key user.",
            details={
                "request_user_id": request.user_id
            }
        )

    # 1. Rate limiting
    rate_limit_status = await check_rate_limit(authenticated_user_id)

    # 2. Prompt risk scanning
    risk = analyze_prompt(request.prompt)

    if risk["action"] == "block":
        client_ip = http_request.client.host if http_request.client else "unknown"

        log_security_alert(
            user_id=authenticated_user_id,
            blocked_prompt=request.prompt,
            attack_type=risk["category"],
            client_ip=client_ip,
            event_type="prompt_blocked",
            severity=risk["risk_level"],
            risk_score=risk["risk_score"],
            action=risk["action"],
            endpoint="/chat",
            details={
                "error_code": "PROMPT_BLOCKED",
                "scanner_category": risk["category"]
            }
        )

        raise_api_error(
            status_code=403,
            error_code="PROMPT_BLOCKED",
            message="Prompt blocked by security policy.",
            details={
                "risk": risk
            }
        )

    # 3. Load LLM API configuration
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    if not api_key:
        raise_api_error(
            status_code=500,
            error_code="LLM_API_KEY_NOT_CONFIGURED",
            message="LLM provider API key is not configured."
        )

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 4. Build conversation history payload
    messages_payload = []

    history = get_recent_history(authenticated_user_id, limit=3)

    for h in history:
        messages_payload.append(
            {
                "role": "user",
                "content": h["prompt"]
            }
        )
        messages_payload.append(
            {
                "role": "assistant",
                "content": h["response"]
            }
        )

    messages_payload.append(
        {
            "role": "user",
            "content": request.prompt
        }
    )

    data = {
        "model": model_name,
        "messages": messages_payload,
        "temperature": 0.7
    }

    # 5. Asynchronous LLM API call with httpx
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=data
            )

        response.raise_for_status()
        response_json = response.json()

        ai_reply = response_json["choices"][0]["message"]["content"]
        tokens_used = response_json["usage"]["total_tokens"]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise_api_error(
                status_code=502,
                error_code="LLM_PROVIDER_AUTH_FAILED",
                message="LLM provider authentication failed."
            )

        raise_api_error(
            status_code=502,
            error_code="LLM_PROVIDER_ERROR",
            message="LLM provider returned an error.",
            details={
                "provider_status_code": e.response.status_code
            }
        )

    except httpx.RequestError:
        raise_api_error(
            status_code=502,
            error_code="LLM_NETWORK_ERROR",
            message="Network error while calling LLM provider."
        )

    except (KeyError, IndexError, TypeError, ValueError):
        raise_api_error(
            status_code=502,
            error_code="LLM_RESPONSE_FORMAT_ERROR",
            message="Unexpected LLM provider response format."
        )

    except Exception:
        raise_api_error(
            status_code=500,
            error_code="LLM_INVOCATION_FAILED",
            message="LLM API invocation failed."
        )

    # 6. Save successful chat log
    log_chat(
        user_id=authenticated_user_id,
        prompt=request.prompt,
        response=ai_reply,
        tokens_used=tokens_used,
        request_status="success",
        risk_score=risk["risk_score"],
        risk_level=risk["risk_level"],
        risk_category=risk["category"],
        risk_action=risk["action"],
        model=model_name
    )

    # 7. Return result
    return {
        "status": "success",
        "reply": ai_reply,
        "tokens_consumed": tokens_used,
        "risk": risk,
        "rate_limit": rate_limit_status,
        "model": model_name
    }