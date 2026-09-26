# Architecture and ERD

This is a local, single-instance LLM security gateway prototype. The diagrams describe the code in this repository, not a hardened production deployment.

## Request and analytics flow

```mermaid
flowchart LR
    Client[API client] --> Chat[POST /chat]
    Admin[Admin API client] --> AdminAPI[GET /admin/logs and /admin/alerts]
    Chat --> Auth[API key authentication]
    Auth --> Limit[Per-user in-memory rate limit]
    Limit --> Scan[Keyword prompt scanner]
    Scan -->|block| Alert[Structured security alert]
    Scan -->|allow or warn| Provider[DeepSeek API]
    Provider --> Log[Successful chat log]
    Alert --> DB[(SQLite)]
    Log --> DB
    AdminAPI --> DB
    Demo[Simulated demo-log generator] --> DB
    DB --> Export[export_logs.py]
    Export --> CSV[Local, ignored CSV exports]
    CSV --> Clean[analyze_logs.py: validate and clean]
    Clean --> Metrics[Descriptive metrics]
    Clean --> Rules[detect_anomalies.py: explainable rules]
    Metrics --> Dashboard[Local Streamlit dashboard]
    Rules --> Dashboard
```

The dashboard reads aggregate and user-level metrics, not raw prompts, responses, or IP addresses. It has no authentication and must remain local-only. The exported CSV files can contain sensitive content and are excluded from Git and Docker builds.

## SQLite entity relationship diagram

```mermaid
erDiagram
    USERS ||--o{ CHAT_LOGS : owns
    USERS ||--o{ SECURITY_ALERTS : triggers

    USERS {
        INTEGER id PK
        TEXT username UK
        TEXT api_key_hash
        INTEGER is_active
        INTEGER is_admin
    }
    CHAT_LOGS {
        INTEGER id PK
        INTEGER user_id FK
        TEXT prompt
        TEXT response
        INTEGER tokens_used
        TEXT request_status
        INTEGER risk_score
        TEXT risk_level
        TEXT risk_category
        TEXT risk_action
        TEXT model
        DATETIME created_at
    }
    SECURITY_ALERTS {
        INTEGER id PK
        INTEGER user_id FK
        TEXT blocked_prompt
        TEXT attack_type
        TEXT client_ip
        TEXT event_type
        TEXT severity
        INTEGER risk_score
        TEXT action
        TEXT endpoint
        TEXT details
        DATETIME timestamp
    }
```

`init_db.py` creates these tables and adds newer columns to older local databases. The `api_key_hash` field is **currently populated and compared as plaintext**, despite its name. Do not interpret the name as a completed hashing control.

## Boundaries and limitations

- `chat_logs` represents successful provider calls. `security_alerts` represents blocked prompts. Missing/invalid API keys, rate-limit rejections, and provider failures are not counted by the current CSV analytics pipeline.
- The anomaly detector is rule-based. A flag is a lead for review, not proof of an attack.
- The Compose configuration binds both web ports to `127.0.0.1` and is intended for local demonstration only. It does not add HTTPS, dashboard authentication, distributed rate limiting, or production-safe key provisioning.
