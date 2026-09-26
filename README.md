# LLM Security Audit Gateway

A FastAPI-based security audit gateway for Large Language Model (LLM) API requests.

This project acts as a middleware layer between users and an external LLM provider. Instead of calling the LLM API directly, requests first pass through this gateway for authentication, rate limiting, prompt risk scanning, logging, and security auditing.

---

## Overview

Directly exposing LLM APIs can create security, privacy, and cost-related risks, such as:

* Unauthorized API access
* Prompt injection attempts
* Sensitive information exposure
* Excessive token usage
* Lack of audit logs
* Inconsistent API error responses

This project provides a lightweight security gateway that helps control, monitor, and audit LLM requests before they reach the external provider.

---

## Key Features

* **API Key Authentication**
  Protects the `/chat` endpoint with an `X-API-Key` request header.

* **User-Based Rate Limiting**
  Limits how many requests each authenticated user can send within a time window.

* **Prompt Risk Scanner**
  Detects basic prompt injection patterns and assigns a risk score, risk level, category, and action.

* **Structured Security Alert Logging**
  Logs blocked prompts with structured fields such as event type, severity, risk score, endpoint, and details.

* **Chat Logging**
  Stores successful chat interactions, including prompt, response, token usage, and timestamp.

* **Sliding Window Memory**
  Retrieves recent chat history to support simple multi-turn conversations.

* **Standardized API Error Responses**
  Returns consistent error objects with `status`, `error_code`, `message`, and `details`.

* **Automated Tests with Pytest**
  Includes tests for authentication, rate limiting, database logging, security alert logging, and error response helpers.

* **Admin Audit Queries**
  Protects `/admin/logs` and `/admin/alerts` with admin API-key verification and filtering.

* **Security Analytics**
  Exports SQLite audit logs to CSV, cleans them with Pandas, computes daily/user metrics, and flags unusual users with explainable rules.

* **Local Dashboard**
  Displays aggregate trends and anomaly leads in Streamlit without showing raw prompts, replies, or IP addresses.

---

## Tech Stack

* Python
* FastAPI
* Pydantic
* SQLite
* DeepSeek API
* httpx
* python-dotenv
* pytest
* pandas
* Streamlit

---

## Project Structure

```text
llm-secure-gateway/
├── auth.py
├── analyze_logs.py
├── detect_anomalies.py
├── export_logs.py
├── generate_demo_logs.py
├── dashboard/
│   ├── app.py
│   └── data.py
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
│   ├── test_rate_limiter.py
│   ├── test_analyze_logs.py
│   ├── test_detect_anomalies.py
│   ├── test_dashboard_app.py
│   ├── test_dashboard_data.py
│   ├── test_database_path.py
│   └── test_demo_analytics_pipeline.py
├── ANALYSIS_REPORT.md
├── ARCHITECTURE.md
├── PORTFOLIO.md
├── Dockerfile
├── compose.yaml
├── .env.example
├── .gitignore
├── pytest.ini
├── README.md
├── requirements-dev.txt
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
Return response to user
```

---

## Environment Variables

Create a local `.env` file based on `.env.example`.

Example:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-v4-flash

RATE_LIMIT_MAX_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=60
```

Important:

```text
Do not commit your real .env file.
Do not commit real API keys.
Only commit .env.example.
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/llm-secure-gateway.git
cd llm-secure-gateway
```

Replace `your-username` with your own GitHub username.

---

### 2. Create a Virtual Environment

For Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

For macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies

Runtime dependencies:

```bash
pip install -r requirements.txt
```

Development dependencies for testing:

```bash
pip install -r requirements-dev.txt
```

---

### 4. Create Local `.env`

For Windows PowerShell:

```powershell
copy .env.example .env
```

For macOS / Linux:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder value with your own local API key.

---

### 5. Initialize the Database

```bash
python init_db.py
```

This creates or updates the local SQLite database:

```text
secure_gateway.db
```

The database file is local only and should not be committed.

---

### 6. Start the FastAPI Server

```bash
uvicorn main:app --reload
```

The server will run at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## API Usage

### Health Check

```text
GET /health
```

Example response:

```json
{
  "status": "ok",
  "service": "LLM Security Audit Gateway"
}
```

---

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
```

---

## Error Response Format

The project uses a standardized API error format:

```json
{
  "detail": {
    "status": "error",
    "error_code": "INVALID_API_KEY",
    "message": "Invalid API key.",
    "details": {}
  }
}
```

Example blocked prompt response:

```json
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
```

---

## Running Tests

Run all tests:

```bash
pytest -v
```

The test suite covers:

* API key authentication
* Missing and invalid API key handling
* Rate limiting
* Chat log database writes
* Structured security alert logging
* Standardized error response helpers
* CSV cleaning, analytics, anomaly rules, and Streamlit rendering with synthetic fixtures

---

## Local Analytics Demo

These commands use local files. The generated demo logs are simulated and must not be presented as real security incidents.

```bash
python generate_demo_logs.py --reset-demo
python export_logs.py
python analyze_logs.py
python detect_anomalies.py
python -m streamlit run dashboard/app.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

The dashboard opens at `http://127.0.0.1:8501`. It has **no login** and must remain local-only. It reads ignored files in `exports/`. Do not commit or publish the CSV exports: they may contain prompts, replies, and IP addresses. `exports/anomalous_users.csv` contains user-level metrics and is also ignored.

The analytics blocked rate counts only successful chats and logged blocked prompts. It does not include invalid API keys, rate-limit rejections, or provider errors. See [the analysis report](ANALYSIS_REPORT.md) and [architecture/ERD](ARCHITECTURE.md).

---

## Deployment

Deployment instructions are available in:

```text
DEPLOYMENT.md
```

The deployment guide covers:

* Local production-like startup
* Environment variable configuration
* SQLite deployment notes
* Cloud deployment preparation
* Post-deployment smoke tests
* Deployment safety checklist

---


## Local Files Not Uploaded to GitHub

The following files should not be committed:

```text
.env
.venv/
__pycache__/
.pytest_cache/
*.pyc
*.db
secure_gateway.db
```

These files may contain secrets, local database records, cache files, or local development artifacts.

---

## Current Status

Implemented:

* FastAPI `/chat` endpoint
* DeepSeek API integration
* SQLite database initialization
* API key authentication
* Prompt risk scanning
* User-based rate limiting
* Chat logging
* Sliding window memory
* Structured security alert logging
* Standardized API error responses
* Pytest test suite
* Admin audit endpoints
* CSV export and simulated demo-log generation
* Pandas statistics and explainable anomaly flags
* Local Streamlit analytics dashboard
* Loopback-only Docker Compose demo configuration

---

## Known Limitations

This is currently a local development prototype.

Known limitations:

* API keys are still stored and compared as plaintext.
* Rate limiting is in-memory and not distributed.
* Prompt scanning is keyword-based.
* The dashboard has no authentication; do not expose it publicly.

---

## Future Improvements

Planned improvements:

* API key hashing
* Redis-based rate limiting
* Dashboard authentication and production-safe deployment
* Additional event logging for authentication failures and rate-limit rejections
* PostgreSQL migration
* More advanced prompt risk scoring

Portfolio-ready project and resume descriptions are in [PORTFOLIO.md](PORTFOLIO.md).

---

## Author

Wenqi Tian
Master of Data Science
Monash University Malaysia
