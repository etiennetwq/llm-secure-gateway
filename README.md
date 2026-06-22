# LLM Secure Gateway

A FastAPI-based LLM Security Audit Gateway.

## Project Overview

This project acts as a security layer between users and external LLM APIs.

Instead of allowing users to directly access the LLM provider, all requests must pass through this gateway.

The gateway performs:

- API Key Authentication
- Prompt Risk Scanning
- Security Alert Logging
- Conversation History Memory
- Token Usage Tracking
- Audit Logging

---

## Architecture

User
↓
FastAPI Gateway
↓
Authentication
↓
Prompt Risk Scanner
↓
Security Decision Engine

 ├── Block → security_alerts
 └── Allow → LLM API

↓
chat_logs
↓
Response

---

## Tech Stack

- Python
- FastAPI
- SQLite
- Pydantic
- DeepSeek API

---

## Database Tables

### users

Stores user identities and API keys.

### chat_logs

Stores successful conversations.

### security_alerts

Stores blocked requests and security incidents.

---

## Features

### Authentication

Users must provide:

X-API-Key

before accessing the chat endpoint.

### Prompt Risk Scanner

Detects potentially risky prompts.

### Audit Logging

All blocked prompts are written into:

security_alerts

### Memory

Recent conversations are retrieved from:

chat_logs

to support multi-turn conversations.

---

## Run

Install dependencies:

pip install -r requirements.txt

Initialize database:

python init_db.py

Start server:

uvicorn main:app --reload

Open Swagger:

http://127.0.0.1:8000/docs

---

## Future Work

- Rate Limiting
- Dashboard
- Docker Deployment
- ML-based Risk Classification
- PostgreSQL Migration

---

## Author

Wenqi Tian
Master of Data Science
Monash University Malaysia