"""Local Streamlit view over exported, cleaned gateway audit logs."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# Keep `streamlit run dashboard/app.py` usable from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = Path(os.getenv("GATEWAY_EXPORT_DIR", str(PROJECT_ROOT / "exports")))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analyze_logs import LogAnalysisError, calculate_metrics, load_and_clean_logs
from dashboard.data import available_date_range, filter_logs_by_date
from detect_anomalies import detect_anomalous_users


def render_dashboard() -> None:
    """Display aggregate trends and rule-based leads without raw prompts or IPs."""

    st.set_page_config(page_title="LLM Security Analytics", layout="wide")
    st.title("LLM Security Analytics")
    st.caption(
        "Local prototype · Data may include simulated demo logs · "
        "Anomaly flags are leads for review, not confirmed attacks."
    )
    st.sidebar.warning(
        "Local use only. This dashboard has no login; do not expose it publicly."
    )

    try:
        logs = load_and_clean_logs(EXPORT_DIR)
    except LogAnalysisError as error:
        st.error(str(error))
        st.info("Export local logs first with `python export_logs.py`.")
        st.stop()

    bounds = available_date_range(logs)
    if bounds:
        start = st.sidebar.date_input(
            "From", value=bounds[0], min_value=bounds[0], max_value=bounds[1]
        )
        end = st.sidebar.date_input(
            "To", value=bounds[1], min_value=bounds[0], max_value=bounds[1]
        )
        if start > end:
            st.error("The start date must not be after the end date.")
            st.stop()
        logs = filter_logs_by_date(logs, start, end)

    metrics = calculate_metrics(logs.chat_logs, logs.security_alerts)
    anomalies = detect_anomalous_users(logs.chat_logs, logs.security_alerts)
    rate = metrics["blocked_rate"]
    tokens = metrics["average_token_usage"]
    cards = st.columns(5)
    cards[0].metric("Logged requests", metrics["total_requests"])
    cards[1].metric("Successful chats", metrics["successful_requests"])
    cards[2].metric("Blocked prompts", metrics["blocked_requests"])
    cards[3].metric("Blocked rate", "N/A" if rate is None else f"{rate:.1%}")
    cards[4].metric("Average tokens", "N/A" if tokens is None else f"{tokens:.0f}")
    st.caption(
        "Blocked rate = blocked prompts / (successful chats + blocked prompts). "
        "Invalid API keys, rate-limit rejections, and provider errors are not in this export."
    )

    daily = metrics["daily_metrics"]
    if daily.empty:
        st.info("No valid events are available for this date range.")
    else:
        left, right = st.columns(2)
        with left:
            st.subheader("Daily logged requests")
            st.line_chart(daily.set_index("date")[["total_requests", "blocked_requests"]])
        with right:
            st.subheader("Daily blocked rate")
            blocked_percent = daily.set_index("date")[["blocked_rate"]] * 100
            st.line_chart(blocked_percent)

    left, right = st.columns(2)
    with left:
        st.subheader("Risk levels")
        risk_levels = metrics["risk_level_distribution"]
        if risk_levels.empty:
            st.info("No risk-level values available.")
        else:
            st.bar_chart(risk_levels.rename("events"))
    with right:
        st.subheader("Attack types")
        attack_types = metrics["attack_type_distribution"]
        if attack_types.empty:
            st.info("No attack-type values available.")
        else:
            st.bar_chart(attack_types.rename("alerts"))

    st.subheader("Users flagged for review")
    if anomalies.empty:
        st.info("No user crossed the current rule thresholds.")
    else:
        st.dataframe(anomalies, hide_index=True)
    st.caption(
        "Default rules: ≥100 logged requests; or ≥20% blocked with ≥5 blocks "
        "and ≥10 requests; or ≥15 high-risk events; or average score ≥60 "
        "across ≥10 scored events."
    )

    st.subheader("User request ranking")
    st.dataframe(metrics["user_request_ranking"].head(20), hide_index=True)
    if logs.warnings:
        with st.expander("Data-quality warnings"):
            for warning in logs.warnings:
                st.write(f"- {warning}")


if __name__ == "__main__":
    render_dashboard()
