from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv

# Import the extracted data persistence and history retrieval functions
from crud import log_chat, get_recent_history

load_dotenv()
app = FastAPI(title="LLM Security Audit Gateway", version="2.0")

class ChatRequest(BaseModel):
    """
    Represents the incoming payload for a chat interaction, providing validation rules.

    Attributes:
        user_id: Must be a valid positive integer to prevent injection
        prompt: The user input, length strictly limited to 1-200 characters to prevent token exhaustion
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

@app.post("/chat")
def chat_endpoint(request: ChatRequest) -> dict:
    """
    Processes incoming chat requests, manages conversational memory, and communicates with the LLM API.

    Args:
        request: The validated incoming chat request payload

    Returns:
        dict:A dictionary containing the status, the LLM's reply, and the token consumption
    """

    # 1. Prepare LLM communication configuration
    api_key = os.getenv("DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    #  Core Modification: Assemble conversational payload with memory
    messages_payload = []
    
    # 1. Retrieve the most recent 3 conversational turns and append to the payload
    history = get_recent_history(request.user_id, limit=3)
    for h in history:
        messages_payload.append({"role": "user", "content": h["prompt"]})
        messages_payload.append({"role": "assistant", "content": h["response"]})
        
    # 2. Append the user's latest prompt to the end of the payload
    messages_payload.append({"role": "user", "content": request.prompt})

    # 3. Construct the memory-augmented data payload
    data = {
        "model": "deepseek-chat",
        "messages": messages_payload,
        "temperature": 0.7
    }
    
    # 2. Dispatch the request to the LLM
    try:
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        ai_reply = response_json['choices'][0]['message']['content']
        tokens_used = response_json['usage']['total_tokens']
        
    except Exception as e:
        # Translate the exception message to English as well
        raise HTTPException(status_code=500, detail=f"LLM API invocation failed: {str(e)}")


    # 3. Persist data to the SQLite database
    log_chat(user_id=request.user_id, prompt=request.prompt, response=ai_reply, tokens_used=tokens_used)

    # 4. Return the execution result
    return {
        "status": "success", 
        "reply": ai_reply, 
        "tokens_consumed": tokens_used
    }