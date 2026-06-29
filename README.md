# LLM Security Audit Gateway

A FastAPI-based security audit gateway for Large Language Model (LLM) API requests.

This project acts as a middleware layer between users and an external LLM API. Instead of allowing users to call the LLM provider directly, all requests must first pass through this gateway for authentication, rate limiting, prompt risk scanning, logging, and security auditing.

---

## Project Overview

Large Language Models are increasingly used in internal tools, customer support systems, and data workflows. However, directly exposing LLM APIs can create security, privacy, and cost-related risks, such as:

- Unauthorized API access
- Prompt injection attempts
- Sensitive information exposure
- Excessive token usage
- Lack of audit logs
- Difficulty monitoring risky user behavior
- Inconsistent API error responses

This project provides a lightweight LLM Security Audit Gateway that helps control and audit LLM requests before they reach the external provider.

---

## Key Features

### 1. API Key Authentication

The `/chat` endpoint requires an API key in the request header:

```text
X-API-Key

If the API key is missing, invalid, or inactive, the request is rejected.

Current prototype note:

API keys are currently stored and compared as plaintext for local development.
A future improvement is to store hashed API keys instead.
2. User-Based Rate Limiting

The gateway includes an in-memory rate limiter.

Default configuration:

RATE_LIMIT_MAX_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=60

If a user exceeds the request limit, the API returns:

429 Too Many Requests

The response also includes a Retry-After header.

Current prototype note:

The rate limiter is currently in-memory and suitable for local single-process development.
A future improvement is to use Redis for distributed deployment.
3. Prompt Risk Scanner

Before forwarding a prompt to the external LLM provider, the gateway analyzes the prompt and assigns a risk result.

The scanner returns:

risk_score
risk_level
category
action

Possible actions:

allow
warn
block

High-risk prompts are blocked before reaching the external LLM provider.

4. Structured Security Alert Logging

Blocked prompts are stored in the security_alerts table for auditing.

The alert log records structured security event information such as:

user_id
blocked_prompt
attack_type
client_ip
event_type
severity
risk_score
action
endpoint
details
timestamp

This makes the project more suitable for later analytics, dashboarding, and security auditing.

5. Chat Logging

Successful LLM interactions are stored in the chat_logs table.

Each chat log records:

user_id
prompt
response
tokens_used
created_at
6. Sliding Window Memory

The gateway retrieves recent conversation history from the database and sends it together with the latest prompt.

This allows the LLM to support simple multi-turn conversations while keeping context size controlled.

7. Standardized API Error Responses

The project uses a consistent error response format:

{
  "detail": {
    "status": "error",
    "error_code": "ERROR_CODE",
    "message": "Human-readable error message.",
    "details": {}
  }
}

This makes errors easier to handle in clients, tests, and future frontend integrations.

8. Automated Tests with Pytest

The project includes pytest tests for:

API key authentication
Rate limiting
Database logging
Security alert logging
Standardized error response helpers
Tech Stack
Python
FastAPI
Pydantic
SQLite
DeepSeek API
httpx
python-dotenv
pytest
Project Structure
llm-secure-gateway/
├── auth.py
├── check_balance.py
├── crud.py
├── database.py
├── errors.py
├── init_db.py
├── main.py
├── prompt_scanner.py
├── rate_limiter.py
├── security_alerts.py
├── test_env.py
├── tests/
│   ├── test_auth.py
│   ├── test_database_logging.py
│   ├── test_error_response_format.py
│   └── test_rate_limiter.py
├── .env.example
├── .gitignore
├── PROJECT_CONTEXT.md
├── PROJECT_STATUS.md
├── pytest.ini
├── README.md
├── requirements-dev.txt
└── requirements.txt
Security Workflow
User Request
    ↓
FastAPI /chat Endpoint
    ↓
API Key Authentication
    ↓
Rate Limiting
    ↓
Prompt Risk Scanner
    ↓
Security Decision
    ├── High Risk → Block request → Log structured security alert
    └── Low Risk → Forward to LLM provider
    ↓
Save successful chat to chat_logs
    ↓
Return standardized response to user
Database Schema

The project uses SQLite for local development.

users

Stores user account information and API keys.

id
username
api_key_hash
is_active
chat_logs

Stores successful LLM conversations.

id
user_id
prompt
response
tokens_used
created_at
security_alerts

Stores structured blocked prompt and security event records.

id
user_id
blocked_prompt
attack_type
client_ip
event_type
severity
risk_score
action
endpoint
details
timestamp
Environment Variables

This project uses environment variables to store sensitive configuration.

Create a local .env file based on .env.example.

Example:

DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-v4-flash

RATE_LIMIT_MAX_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=60

Important:

Do not commit your real .env file.
Do not commit real API keys.
Only commit .env.example.
Installation
1. Clone the Repository
git clone https://github.com/your-username/llm-secure-gateway.git
cd llm-secure-gateway

Replace your-username with your own GitHub username.

2. Create a Virtual Environment

For Windows PowerShell:

python -m venv .venv
.venv\Scripts\activate

For macOS / Linux:

python3 -m venv .venv
source .venv/bin/activate
3. Install Runtime Dependencies
pip install -r requirements.txt
4. Install Development Dependencies

For running tests:

pip install -r requirements-dev.txt
5. Create Local .env

For Windows PowerShell:

copy .env.example .env

For macOS / Linux:

cp .env.example .env

Then open .env and replace the placeholder value with your own local API key.

Do not upload the real .env file to GitHub.

6. Initialize the Database
python init_db.py

This creates or updates the local SQLite database:

secure_gateway.db

The database file is local only and should not be committed.

7. Start the FastAPI Server
uvicorn main:app --reload

The server will run at:

http://127.0.0.1:8000
8. Open Swagger UI

Open:

http://127.0.0.1:8000/docs

You can test API endpoints directly from the browser.

API Usage
Health Check
GET /health

Example response:

{
  "status": "ok",
  "service": "LLM Security Audit Gateway"
}
Chat Endpoint
POST /chat

Required header:

X-API-Key: test_token_123

Example request body:

{
  "user_id": 1,
  "prompt": "What is data science?"
}

Example successful response:

{
  "status": "success",
  "reply": "Data science is ...",
  "tokens_consumed": 1187,
  "risk": {
    "risk_score": 0,
    "risk_level": "low",
    "category": "normal",
    "action": "allow"
  },
  "rate_limit": {
    "limit": 5,
    "window_seconds": 60,
    "remaining_requests": 4
  },
  "model": "deepseek-v4-flash"
}
Example Error Response

Example invalid API key response:

{
  "detail": {
    "status": "error",
    "error_code": "INVALID_API_KEY",
    "message": "Invalid API key.",
    "details": {}
  }
}

Example blocked prompt response:

{
  "detail": {
    "status": "error",
    "error_code": "PROMPT_BLOCKED",
    "message": "Prompt blocked by security policy.",
    "details": {
      "risk": {
        "risk_score": 70,
        "risk_level": "high",
        "category": "prompt_injection",
        "action": "block"
      }
    }
  }
}
Running Tests

Run all tests:

pytest -v

The test suite covers:

Authentication
Missing API key handling
Invalid API key handling
Rate limiting
Database chat logging
Structured security alert logging
Standardized error response helpers
Example Test Scenarios
1. Valid Chat Request

Expected result:

200 OK

The prompt is scanned, forwarded to the LLM provider, and logged in chat_logs.

2. Invalid API Key

Expected result:

401 Unauthorized

The API returns a standardized error response.

3. Rate Limit Exceeded

Expected result:

429 Too Many Requests

The response includes a Retry-After header.

4. High-Risk Prompt

Expected result:

403 Forbidden

The prompt is blocked and a structured security alert is written to security_alerts.

Local Files Not Uploaded to GitHub

The following files should not be uploaded to GitHub:

.env
.venv/
__pycache__/
.pytest_cache/
*.pyc
*.db
secure_gateway.db

These files may contain secrets, local database records, cached files, or local development artifacts.

Current Status

Implemented:

FastAPI /chat endpoint
DeepSeek API integration
SQLite database initialization
Chat log storage
Sliding window conversation memory
API key authentication
Basic prompt risk scanning
Security alert logging
Structured security alert logs
User-based rate limiting
Standardized API error responses
Pytest test suite
Known Limitations

This is currently a local development prototype.

Known limitations:

API keys are still stored and compared as plaintext.
Rate limiter is in-memory and not distributed.
Deployment instructions are not fully added yet.
Future Improvements

Planned improvements:

Deployment instructions
GitHub portfolio description
API key hashing
Redis-based rate limiting
Admin log query endpoint
Security analytics dashboard
Token usage statistics
Risk category visualization
Docker support
PostgreSQL migration
More advanced prompt risk scoring
ML-based anomaly detection
Learning Goals

This project is designed to practice:

Python backend development
FastAPI API design
SQLite database operations
API authentication
Secure environment variable management
LLM API integration
Prompt risk detection
Rate limiting
Security audit logging
Automated testing with pytest
Author

Wenqi Tian
Master of Data Science
Monash University Malaysia