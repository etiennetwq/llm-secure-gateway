# LLM Secure Gateway

A FastAPI-based security audit gateway for Large Language Model (LLM) API requests.

This project acts as a middleware layer between users and an external LLM API. Instead of allowing users to call the LLM provider directly, all requests must first pass through this gateway for authentication, prompt risk scanning, logging, and security auditing.

---

## Project Overview

Many organizations are starting to use LLMs in internal tools, customer service systems, and data workflows. However, directly exposing LLM APIs can create security and cost-related risks, such as:

* Unauthorized API access
* Prompt injection attempts
* Sensitive information exposure
* Excessive token usage
* Lack of audit logs
* Difficulty monitoring risky user behavior

This project aims to build a lightweight LLM security gateway that can:

* Authenticate users with API keys
* Scan prompts before sending them to the LLM
* Block high-risk prompts
* Log blocked prompts as security alerts
* Store successful chat interactions
* Track token usage
* Support basic conversation memory

---

## Key Features

### 1. API Key Authentication

The `/chat` endpoint requires an API key in the request header.

Header name:

```text
X-API-Key
```

If the API key is missing or invalid, the request will be rejected.

---

### 2. Prompt Risk Scanner

Before forwarding a prompt to the LLM API, the gateway analyzes the prompt and assigns a risk result.

The scanner returns:

```text
risk_score
risk_level
category
action
```

Possible actions:

```text
allow
warn
block
```

High-risk prompts are blocked before reaching the external LLM API.

---

### 3. Security Alert Logging

Blocked prompts are stored in the `security_alerts` table for auditing.

The alert log stores information such as:

* User ID
* Blocked prompt
* Attack type
* Client IP address
* Timestamp

---

### 4. Chat Logging

Successful LLM interactions are stored in the `chat_logs` table.

Each chat log records:

* User ID
* Prompt
* LLM response
* Tokens used
* Timestamp

---

### 5. Sliding Window Memory

The gateway retrieves recent conversation history from the database and sends it together with the latest prompt.

This allows the LLM to support simple multi-turn conversations while keeping the context size controlled.

---

## Tech Stack

* Python
* FastAPI
* Pydantic
* SQLite
* DeepSeek API
* python-dotenv
* requests

---

## Project Structure

Current project structure:

```text
llm-secure-gateway/
├── auth.py
├── check_balance.py
├── crud.py
├── database.py
├── init_db.py
├── main.py
├── prompt_scanner.py
├── security_alerts.py
├── test_env.py
├── README.md
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Security Workflow

```text
User Request
    ↓
FastAPI /chat Endpoint
    ↓
API Key Authentication
    ↓
Prompt Risk Scanner
    ↓
Security Decision
    ├── High Risk → Block request → Log to security_alerts
    └── Low Risk → Forward to LLM API
    ↓
Save successful chat to chat_logs
    ↓
Return response to user
```

---

## Database Schema

The project uses SQLite for local development.

### users

Stores user account information and API keys.

```text
id
username
api_key_hash
is_active
```

### chat_logs

Stores successful LLM conversations.

```text
id
user_id
prompt
response
tokens_used
created_at
```

### security_alerts

Stores blocked prompts and security events.

```text
id
user_id
blocked_prompt
attack_type
client_ip
timestamp
```

---

## Environment Variables

This project uses environment variables to store sensitive configuration such as API keys.

Create a `.env` file based on `.env.example`.

### `.env.example`

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### Local `.env`

Create a real `.env` file in the project root:

```env
DEEPSEEK_API_KEY=your_real_deepseek_api_key
```

Important:

* Do not upload the real `.env` file to GitHub.
* Only upload `.env.example`.
* Keep your real API key private.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/etiennetwq/llm-secure-gateway
cd llm-secure-gateway
```

Replace `your-username` with your own GitHub username.

---

### 2. Create a virtual environment

For Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` has not been created yet, install the main dependencies manually:

```bash
pip install fastapi uvicorn pydantic requests python-dotenv
```

---

### 4. Create the `.env` file

For Windows PowerShell:

```powershell
copy .env.example .env
```

Then open `.env` and replace the placeholder with your own DeepSeek API key.

---

### 5. Initialize the database

```bash
python init_db.py
```

This will create the local SQLite database and initialize the required tables.

---

### 6. Start the FastAPI server

```bash
uvicorn main:app --reload
```

The server will run at:

```text
http://127.0.0.1:8000
```

---

### 7. Open Swagger UI

Open the following URL in your browser:

```text
http://127.0.0.1:8000/docs
```

You can test the API endpoints directly from Swagger UI.

---

## API Usage

### Chat Endpoint

```text
POST /chat
```

Required header:

```text
X-API-Key: test_token_123
```

Example request body:

```json
{
  "user_id": 1,
  "prompt": "What is data science?"
}
```

Example successful response:

```json
{
  "status": "success",
  "reply": "Data science is ...",
  "tokens_consumed": 1187
}
```

---

## Example Test Cases

### 1. Valid request

A normal prompt should pass authentication, be sent to the LLM API, and be logged in `chat_logs`.

Example prompt:

```text
What is data science?
```

Expected result:

```text
200 OK
```

---

### 2. Invalid API key

A request with an incorrect API key should be rejected.

Expected result:

```text
401 Unauthorized
```

---

### 3. High-risk prompt

A high-risk prompt should be blocked before reaching the external LLM API.

Expected result:

```text
403 Forbidden
```

The blocked prompt should be logged in the `security_alerts` table.

---

## Local Files Not Uploaded to GitHub

The following files should not be uploaded to GitHub:

```text
.env
.venv/
__pycache__/
*.pyc
*.db
secure_gateway.db
```

These files are local development files and may contain sensitive information, API keys, cached files, or local database records.

---

## Current Status

Implemented:

* FastAPI `/chat` endpoint
* DeepSeek API integration
* SQLite database initialization
* Chat log storage
* Sliding window conversation memory
* API key authentication
* Basic prompt risk scanning
* Security alert logging for blocked prompts

---

## Future Improvements

Planned improvements:

* Rate limiting
* Admin log query endpoint
* Streamlit analytics dashboard
* Token usage statistics
* Risk category visualization
* Docker support
* Unit tests with pytest
* API key hashing
* PostgreSQL migration
* More advanced prompt risk scoring
* ML-based anomaly detection

---

## Learning Goals

This project is designed to practice:

* Python backend development
* FastAPI API design
* SQLite database operations
* API authentication
* Secure environment variable management
* LLM API integration
* Prompt risk detection
* Security audit logging
* Data science applied to security logs

---

## Author

Wenqi Tian 
Master of Data Science
Monash University Malaysia
