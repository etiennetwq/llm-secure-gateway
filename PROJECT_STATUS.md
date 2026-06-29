# LLM Security Audit Gateway - Project Status

## Current Version

v0.2.6

## Project Goal

A FastAPI-based LLM Security Audit Gateway with API key authentication, prompt scanning, security alert logging, rate limiting, chat logging, and basic auditability for LLM requests.

## Completed Features

* API key authentication implemented in auth.py
* Prompt scanner implemented in prompt_scanner.py
* Security alert logging implemented in security_alerts.py
* Rate limiter added in rate_limiter.py
* Basic environment variable loading added
* README.md created
* `/health` endpoint implemented in main.py
* Pytest configuration added in pytest.ini
* Development dependency file added in requirements-dev.txt
* Automated pytest tests added for API key authentication
* Automated pytest tests added for rate limiting
* Automated pytest tests added for chat_logs database logging
* Automated pytest tests added for security_alerts database logging
* Standardized API error response format added in errors.py
* Auth error responses standardized
* Rate limit error responses standardized
* Chat endpoint error responses standardized
* Pytest tests added for standardized error response format
* Structured security alert logs added
* README setup instructions improved
* Deployment instructions added in DEPLOYMENT.md

## Recent Fixes

* 2026-06-25: Replaced exposed API key and updated .env.example
* 2026-06-25: Added rate limiting middleware / dependency
* 2026-06-25: Verified rate limit returns 429 after exceeding limit
* 2026-06-27: Added pytest tests for auth.py using a temporary SQLite database and monkeypatching
* 2026-06-27: Added pytest tests for rate_limiter.py covering allowed requests, exceeded limits, separate users, and expired windows
* 2026-06-27: Removed FastAPI TestClient usage from auth tests to avoid Starlette deprecation warning
* 2026-06-27: Verified pytest result: 8 passed with no warning
* 2026-06-28: Added pytest tests for chat_logs and security_alerts database logging
* 2026-06-28: Verified database logging tests pass with pytest
* 2026-06-28: Added errors.py for standardized API error responses
* 2026-06-28: Standardized error responses in auth.py, rate_limiter.py, and main.py
* 2026-06-28: Updated auth and rate limiter tests for the new error response format
* 2026-06-28: Added pytest tests for error response helper functions
* 2026-06-29: Added structured fields to security alert logging
* 2026-06-29: Updated blocked prompt logging to include event_type, severity, risk_score, action, endpoint, and details
* 2026-06-29: Updated database logging tests for structured security alerts
* 2026-06-29: Improved README setup instructions, API usage documentation, test instructions, and project structure.
* 2026-06-29: Added DEPLOYMENT.md with local deployment, cloud deployment preparation, environment variable setup, smoke tests, and deployment safety checklist.
* 2026-06-29: Added README deployment reference section.

## Known Issues

* API key is still stored and compared as plaintext in the current local prototype; should be upgraded to hashed API key storage later
* Rate limiter is currently in-memory and suitable for local/single-process development only

## Next Tasks

1. Prepare GitHub portfolio description

## Important Decisions

* Do not upload real .env files to GitHub or ChatGPT Project Sources
* Use .env.example only for environment variable examples
* Do not commit secure_gateway.db or other local database files
* Use FastAPI dependency-based API key verification
* Keep commit messages concise and conventional-style
* Treat PROJECT_STATUS.md as the source of truth for project progress
* Trust latest uploaded source files and PROJECT_STATUS.md over older chat history
