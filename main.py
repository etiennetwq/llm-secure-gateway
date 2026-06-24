from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field
import os
import httpx
from dotenv import load_dotenv

from crud import log_chat, get_recent_history
from auth import verify_api_key
from prompt_scanner import analyze_prompt
from security_alerts import log_security_alert
from rate_limiter import check_rate_limit


load_dotenv()

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
        raise HTTPException(
            status_code=403,
            detail="The request user_id does not match the authenticated API key user."
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
            client_ip=client_ip
        )

        raise HTTPException(
            status_code=403,
            detail={
                "message": "Prompt blocked",
                "risk": risk
            }
        )

    # 2. Load LLM API configuration
    api_key = os.getenv("DEEPSEEK_API_KEY")
    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="DEEPSEEK_API_KEY is not configured."
        )

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 3. Build conversation history payload
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

    # 4. Asynchronous LLM API call with httpx
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
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "message": "LLM API returned an error.",
                "error": e.response.text
            }
        )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Network error while calling LLM API: {str(e)}"
        )

    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected LLM API response format: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM API invocation failed: {str(e)}"
        )

    # 5. Save successful chat log
    log_chat(
        user_id=authenticated_user_id,
        prompt=request.prompt,
        response=ai_reply,
        tokens_used=tokens_used
    )

    # 6. Return result
    return {
        "status": "success",
        "reply": ai_reply,
        "tokens_consumed": tokens_used,
        "risk": risk,
        "rate_limit": rate_limit_status,
        "model": model_name
    }