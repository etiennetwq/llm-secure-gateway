# Portfolio Description

## GitHub repository description

FastAPI LLM security gateway with audit logging, Pandas analytics, explainable anomaly flags, and a local Streamlit dashboard.

## Project overview

Built a local LLM Security Audit Gateway that authenticates clients, limits requests per user, scans prompts for basic injection keywords, blocks and records high-risk requests, and logs successful LLM interactions. A separate analytics pipeline exports SQLite audit records, validates and cleans CSV data with Pandas, computes user and daily security metrics, applies explainable rule-based anomaly flags, and presents aggregate results in Streamlit. Automated tests include an isolated synthetic database-to-analytics pipeline and a separate dashboard rendering check. See `ARCHITECTURE.md` and `ANALYSIS_REPORT.md` for implementation and evidence.

## Resume bullet examples

- Developed a FastAPI gateway with API-key checks, per-user rate limiting, prompt-risk decisions, structured SQLite audit logs, and admin-only log query endpoints.
- Built a Pandas pipeline for log validation, data-quality warnings, blocked-rate and token-use statistics, daily trends, and explainable user-level anomaly flags; visualized aggregate results in a local Streamlit dashboard.
- Added automated tests using temporary databases and synthetic CSV fixtures, and packaged a loopback-only local demo with Docker Compose.

## Honest scope statement

This is a **portfolio prototype**, not a production security product. The demo dataset is simulated, the scanner is keyword-based, API keys remain plaintext in the local prototype, the rate limiter is process-local, and the Streamlit dashboard has no login. The Compose example is bound to localhost. Do not claim production deployment, ML-based attack detection, or measured real-world detection accuracy.
