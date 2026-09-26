# Security Log Analysis Report

## Scope and evidence

This report documents the **simulated-data demonstration** of the security analytics pipeline. It does not claim findings from production traffic. The repeatable end-to-end test in `tests/test_demo_analytics_pipeline.py` initializes a temporary SQLite database, generates 30 inactive demo users, 1,000 successful chat rows and 120 blocked-prompt alert rows with seed 42, exports both tables, cleans them with Pandas, and runs the rule-based detector. No real provider call or local private database is used by this test.

The test establishes 1,120 logged events and a blocked-prompt share of `120 / 1120 = 10.71%`. This proportion is a consequence of the **chosen simulation inputs**, not an estimate of real-world attack frequency or scanner effectiveness. Generated timestamps are relative to execution time, so daily totals depend on when the demo is run.

## Pipeline

1. `export_logs.py` writes `chat_logs.csv` and `security_alerts.csv` from SQLite.
2. `analyze_logs.py` checks required columns; trims text; converts empty strings to missing values; parses timestamps and numeric fields; warns about invalid values; and drops rows without essential identifiers or dates.
3. Descriptive statistics combine successful chats and blocked alerts into one event table. They include total events, blocked rate, risk and attack-type distributions, average tokens per successful chat, user rankings, and daily request/risk trends.
4. `detect_anomalies.py` groups events by user and records every rule triggered. The dashboard uses the same cleaned inputs and rules.

## Rule-based findings for review

The defaults flag a user if any of these conditions is met:

| Rule | Default condition | Interpretation |
|---|---|---|
| `high_volume` | At least 100 logged events | Unusually high activity for this **demo threshold** |
| `high_blocked_rate` | At least 10 events, 5 blocks, and 20% blocked | Repeated blocked prompts with a meaningful denominator |
| `repeated_high_risk` | At least 15 high-risk events | Persistent elevated-risk activity |
| `high_average_risk` | Mean risk score at least 60 across 10 scored events | Sustained elevated score, excluding missing scores |

The detector outputs the observed counts, rates, average score, number of triggered rules, and reason names. Its test suite verifies rule explanations, ranking, missing scores, empty inputs, threshold validation, and temporary CSV input. The demo generator deliberately weights a few user profiles toward high volume and risky behavior, so the existence of flags in the demonstration is expected; it does **not** measure detection precision or recall.

## Data-quality and interpretation limits

- The denominator of blocked rate is **successful chats plus logged blocked prompts**. Authentication failures, 429 responses, and provider errors are absent; this is not an all-HTTP-request block rate.
- Some older rows may lack optional risk fields. Missing scores are not silently replaced with zero; warnings are emitted and averages use only scored events.
- The scanner is keyword-based, and simulated risk labels are not ground-truth attack labels.
- Local CSVs may contain prompts, responses, and IP addresses. They are ignored by Git, and this report intentionally contains no private log excerpts or user identifiers.
- Fixed demo thresholds are explanatory examples, not calibrated security policy. A real deployment would need labeled data, false-positive review, operational baselines, and stronger logging coverage.

## Reproduce locally

Install `requirements-dev.txt`, then run `python -m pytest tests/test_demo_analytics_pipeline.py -v` to exercise the isolated synthetic pipeline. For an existing **local-only** database, run `python export_logs.py`, `python analyze_logs.py`, and `python detect_anomalies.py`. The latter creates an ignored `exports/anomalous_users.csv` with metrics only. Open the dashboard with `python -m streamlit run dashboard/app.py --server.address=127.0.0.1 --browser.gatherUsageStats=false`.

Next analytical work should distinguish real from simulated data, log additional rejection types if their rates matter, and validate anomaly thresholds against reviewed events before using flags operationally.
