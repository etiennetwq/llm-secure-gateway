# Deployment Guide

This document explains how to deploy the LLM Security Audit Gateway for a local production-like environment and how to prepare it for a cloud deployment.

The current project is a local development prototype using FastAPI, SQLite, API key authentication, prompt risk scanning, rate limiting, structured security alert logging, and standardized API error responses.

---

## 1. Deployment Scope

This guide covers:

* Running the gateway locally in a production-like mode
* Preparing environment variables safely
* Initializing the SQLite database
* Running the FastAPI server
* Basic cloud deployment considerations
* Post-deployment smoke tests
* Deployment safety checklist

Current limitations:

* SQLite is used for local development.
* API keys are still stored and compared as plaintext.
* Rate limiting is currently in-memory and not distributed.

For a real production deployment, future improvements should include:

* Hashed API key storage
* PostgreSQL or another managed database
* Redis-based distributed rate limiting
* Centralized logging and monitoring
* HTTPS termination through a trusted hosting provider or reverse proxy

---

## 2. Required Environment Variables

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

## 3. Local Production-Like Deployment

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/llm-secure-gateway.git
cd llm-secure-gateway
```

Replace `your-username` with your own GitHub username.

---

### Step 2: Create a Virtual Environment

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

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

For development and testing:

```bash
pip install -r requirements-dev.txt
```

---

### Step 4: Create Local `.env`

For Windows PowerShell:

```powershell
copy .env.example .env
```

For macOS / Linux:

```bash
cp .env.example .env
```

Then edit `.env` and add your real local API key.

Do not commit `.env`.

---

### Step 5: Initialize the Database

```bash
python init_db.py
```

This creates or updates the local SQLite database:

```text
secure_gateway.db
```

The database file is local only and should not be committed.

---

### Step 6: Run Tests Before Deployment

```bash
pytest -v
```

All tests should pass before starting the server.

---

### Step 7: Start the Server

For local production-like testing:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## 4. Cloud Deployment Preparation

For a cloud platform, configure the following settings in the platform dashboard.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

If the platform does not provide `$PORT`, use:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Required Environment Variables

Add these in the hosting platform's environment variable settings:

```text
DEEPSEEK_API_KEY
DEEPSEEK_MODEL
RATE_LIMIT_MAX_REQUESTS
RATE_LIMIT_WINDOW_SECONDS
```

Never upload a real `.env` file to the hosting platform repository.

---

## 5. SQLite Deployment Note

This project currently uses SQLite for local development.

SQLite is acceptable for:

* Local testing
* Portfolio demos
* Single-instance development environments

SQLite is not ideal for:

* Multi-instance deployment
* High traffic production workloads
* Cloud platforms with ephemeral file systems
* Long-term persistent audit logs

For a more production-ready deployment, migrate the database layer to PostgreSQL or another managed database.

---

## 6. Post-Deployment Smoke Tests

After starting the server, run these basic checks.

### 1. Health Check

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "LLM Security Audit Gateway"
}
```

---

### 2. Missing or Invalid API Key

Send a `/chat` request without a valid `X-API-Key`.

Expected result:

```text
401 Unauthorized
```

Expected standardized error format:

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

---

### 3. Valid Chat Request

Send a valid request with:

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

Expected result:

```text
200 OK
```

The request should pass authentication, rate limiting, prompt scanning, and then be forwarded to the LLM provider.

---

### 4. High-Risk Prompt

Send a prompt containing high-risk prompt injection patterns.

Expected result:

```text
403 Forbidden
```

The prompt should be blocked and logged into the `security_alerts` table as a structured security alert.

---

### 5. Rate Limit Check

Send more requests than the configured limit within the configured time window.

Expected result:

```text
429 Too Many Requests
```

The response should include a `Retry-After` header.

---

## 7. Deployment Safety Checklist

Before deploying or sharing the repository, confirm:

```text
.env is not committed
secure_gateway.db is not committed
real API keys are not committed
.pytest_cache/ is not committed
.venv/ is not committed
__pycache__/ is not committed
```

Check Git status:

```bash
git status
```

Check whether sensitive local files are tracked:

```bash
git ls-files .env secure_gateway.db
```

If this command returns output, remove those files from Git tracking:

```bash
git rm --cached .env secure_gateway.db
```

Then commit the cleanup.

---

## 8. Suggested Future Production Improvements

For a stronger production version, consider:

* Store API keys as hashes instead of plaintext
* Replace SQLite with PostgreSQL
* Replace in-memory rate limiting with Redis
* Add structured application logging
* Add a production-safe bootstrap process instead of a predictable seeded admin key
* Add authentication to the Streamlit dashboard before any non-local access
* Add CI tests with GitHub Actions
* Add deployment-specific environment validation
* Disable or restrict public Swagger UI in production

---

## 9. Docker Compose: local demo only

`compose.yaml` starts the API and Streamlit dashboard on **127.0.0.1 only**. It persists the SQLite database and CSV exports in named volumes. This is not a production deployment: `init_db.py` still seeds a predictable local test administrator, API keys remain plaintext, rate limiting is in-memory, and the dashboard has no login. Do not change the port bindings to public interfaces without fixing these limitations.

Create a local `.env` from `.env.example` and set your own provider key; `.env` is excluded from Git and the Docker build context. Then:

```bash
docker compose up --build -d
docker compose ps
```

The API health endpoint is at `http://127.0.0.1:8000/health`; the dashboard is at `http://127.0.0.1:8501`. To export container-local logs into the shared dashboard volume after generating local activity:

```bash
docker compose exec gateway python export_logs.py --db /app/data/secure_gateway.db --output-dir /app/exports
```

The dashboard will report missing CSV files until the export has run. For a synthetic-only demo inside the container, you can first run:

```bash
docker compose exec gateway python generate_demo_logs.py --db /app/data/secure_gateway.db --reset-demo
docker compose exec gateway python export_logs.py --db /app/data/secure_gateway.db --output-dir /app/exports
```

`docker compose down` stops the services while leaving the named data volumes in place. Never commit `.env`, the SQLite database, or exported CSVs.
