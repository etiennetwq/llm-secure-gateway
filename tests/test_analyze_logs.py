from __future__ import annotations

import pandas as pd
import pytest

from analyze_logs import (
    LogAnalysisError,
    calculate_metrics,
    clean_chat_logs,
    clean_security_alerts,
    load_and_clean_logs,
)


def write_csv(path, content: str) -> None:
    """Write UTF-8 CSV fixture content to a temporary path."""

    path.write_text(content, encoding="utf-8")


def test_load_and_clean_logs_handles_normal_csv_data(tmp_path):
    write_csv(
        tmp_path / "chat_logs.csv",
        "user_id,created_at,tokens_used,risk_score,risk_level\n"
        "1,2026-07-01 10:00:00,100,0,low\n"
        "2,2026-07-01 11:00:00,200,50,medium\n"
    )
    write_csv(
        tmp_path / "security_alerts.csv",
        "user_id,timestamp,attack_type,risk_score,severity\n"
        "2,2026-07-01 12:00:00,prompt_injection,100,high\n"
    )

    cleaned = load_and_clean_logs(tmp_path)
    metrics = calculate_metrics(cleaned.chat_logs, cleaned.security_alerts)

    assert len(cleaned.chat_logs) == 2
    assert len(cleaned.security_alerts) == 1
    assert metrics["total_requests"] == 3
    assert metrics["successful_requests"] == 2
    assert metrics["blocked_requests"] == 1
    assert metrics["average_token_usage"] == 150.0


def test_empty_csv_with_headers_produces_zero_metrics(tmp_path):
    write_csv(
        tmp_path / "chat_logs.csv",
        "user_id,created_at,tokens_used,risk_score,risk_level\n"
    )
    write_csv(
        tmp_path / "security_alerts.csv",
        "user_id,timestamp,attack_type,risk_score,severity\n"
    )

    cleaned = load_and_clean_logs(tmp_path)
    metrics = calculate_metrics(cleaned.chat_logs, cleaned.security_alerts)

    assert metrics["total_requests"] == 0
    assert metrics["blocked_rate"] is None
    assert metrics["daily_metrics"].empty


def test_missing_required_field_raises_clear_error(tmp_path):
    write_csv(tmp_path / "chat_logs.csv", "user_id,tokens_used\n1,100\n")
    write_csv(
        tmp_path / "security_alerts.csv",
        "user_id,timestamp,attack_type\n1,2026-07-01,prompt_injection\n"
    )

    with pytest.raises(LogAnalysisError, match="created_at"):
        load_and_clean_logs(tmp_path)


def test_cleaning_removes_missing_values_and_invalid_timestamps():
    chat_logs = pd.DataFrame(
        {
            "user_id": ["1", "", "2"],
            "created_at": ["2026-07-01", "2026-07-01", "invalid-date"],
            "tokens_used": ["20", "", "not-a-number"],
            "risk_score": ["0", "", "bad"],
            "risk_level": ["low", "", "medium"]
        }
    )
    warnings: list[str] = []

    cleaned = clean_chat_logs(chat_logs, warnings)

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["user_id"] == 1
    assert cleaned.iloc[0]["tokens_used"] == 20
    assert any("invalid 'created_at'" in warning for warning in warnings)
    assert any("removed 2 row" in warning for warning in warnings)


def test_cleaning_reports_invalid_numeric_values():
    alerts = pd.DataFrame(
        {
            "user_id": ["1"],
            "timestamp": ["2026-07-01"],
            "attack_type": ["prompt_injection"],
            "risk_score": ["not-a-number"]
        }
    )
    warnings: list[str] = []

    cleaned = clean_security_alerts(alerts, warnings)

    assert len(cleaned) == 1
    assert pd.isna(cleaned.iloc[0]["risk_score"])
    assert any("invalid 'risk_score'" in warning for warning in warnings)


def test_cleaning_warns_when_optional_metric_field_is_missing():
    chat_logs = pd.DataFrame(
        {
            "user_id": ["1"],
            "created_at": ["2026-07-01"],
            "tokens_used": ["20"],
            "risk_score": ["0"]
        }
    )
    warnings: list[str] = []

    clean_chat_logs(chat_logs, warnings)

    assert any("optional column 'risk_level'" in warning for warning in warnings)


def test_blocked_rate_is_calculated_correctly():
    chat_logs = pd.DataFrame(
        {
            "user_id": [1, 2, 3],
            "created_at": pd.to_datetime(["2026-07-01"] * 3),
            "tokens_used": [10, 20, 30],
            "risk_score": [0, 0, 50],
            "risk_level": ["low", "low", "medium"]
        }
    )
    alerts = pd.DataFrame(
        {
            "user_id": [2, 3],
            "timestamp": pd.to_datetime(["2026-07-01"] * 2),
            "attack_type": ["prompt_injection", "secret_extraction"],
            "risk_score": [100, 80],
            "severity": ["high", "high"]
        }
    )

    metrics = calculate_metrics(chat_logs, alerts)

    assert metrics["blocked_rate"] == pytest.approx(2 / 5)
    assert metrics["daily_metrics"].iloc[0]["blocked_rate"] == pytest.approx(2 / 5)


def test_high_risk_user_ranking_combines_blocked_and_high_risk_events():
    chat_logs = pd.DataFrame(
        {
            "user_id": [1, 2],
            "created_at": pd.to_datetime(["2026-07-01", "2026-07-01"]),
            "tokens_used": [10, 20],
            "risk_score": [90, 0],
            "risk_level": ["high", "low"]
        }
    )
    alerts = pd.DataFrame(
        {
            "user_id": [2, 2, 3],
            "timestamp": pd.to_datetime(["2026-07-01"] * 3),
            "attack_type": ["prompt_injection"] * 3,
            "risk_score": [100, 80, 70],
            "severity": ["high"] * 3
        }
    )

    ranking = calculate_metrics(chat_logs, alerts)["high_risk_user_ranking"]

    assert ranking.to_dict("records") == [
        {"user_id": 2, "high_risk_event_count": 2},
        {"user_id": 1, "high_risk_event_count": 1},
        {"user_id": 3, "high_risk_event_count": 1}
    ]
