"""Tests for explainable, user-level anomaly flags."""

from __future__ import annotations

import pandas as pd
import pytest

from analyze_logs import load_and_clean_logs
from detect_anomalies import (
    AnomalyThresholds,
    build_user_risk_profile,
    detect_anomalous_users,
)


def test_flags_high_volume_and_blocked_rate_with_reasons() -> None:
    chats = pd.DataFrame(
        {
            "user_id": [1] * 4 + [2] * 2,
            "created_at": pd.to_datetime(["2026-07-01"] * 6),
            "risk_score": [0] * 6,
            "risk_level": ["low"] * 6,
        }
    )
    alerts = pd.DataFrame(
        {
            "user_id": [1] * 2,
            "timestamp": pd.to_datetime(["2026-07-01"] * 2),
            "attack_type": ["prompt_injection"] * 2,
            "risk_score": [100] * 2,
            "severity": ["high"] * 2,
        }
    )
    limits = AnomalyThresholds(
        high_volume_requests=6,
        min_requests_for_blocked_rate=5,
        min_blocked_requests=2,
        blocked_rate=0.3,
        high_risk_events=3,
        min_scored_events=5,
        average_risk_score=50,
    )

    flagged = detect_anomalous_users(chats, alerts, limits)

    assert flagged["user_id"].tolist() == [1]
    assert flagged.iloc[0]["request_count"] == 6
    assert flagged.iloc[0]["blocked_rate"] == pytest.approx(2 / 6)
    assert flagged.iloc[0]["rule_count"] == 2
    assert flagged.iloc[0]["reasons"] == "high_volume, high_blocked_rate"


def test_ranking_prioritizes_more_triggered_rules() -> None:
    chats = pd.DataFrame(
        {
            "user_id": [1, 1, 2, 2, 2],
            "created_at": pd.to_datetime(["2026-07-01"] * 5),
            "risk_score": [0, 0, 80, 80, 80],
            "risk_level": ["low", "low", "high", "high", "high"],
        }
    )
    alerts = pd.DataFrame(
        {
            "user_id": [1, 2, 2],
            "timestamp": pd.to_datetime(["2026-07-01"] * 3),
            "attack_type": ["prompt_injection"] * 3,
            "risk_score": [100] * 3,
            "severity": ["high"] * 3,
        }
    )
    limits = AnomalyThresholds(
        high_volume_requests=5,
        min_requests_for_blocked_rate=3,
        min_blocked_requests=1,
        blocked_rate=0.2,
        high_risk_events=3,
        min_scored_events=3,
        average_risk_score=60,
    )

    flagged = detect_anomalous_users(chats, alerts, limits)

    assert flagged["user_id"].tolist() == [2, 1]
    assert flagged.iloc[0]["rule_count"] == 4
    assert flagged.iloc[1]["rule_count"] == 1


def test_empty_logs_and_missing_optional_scores() -> None:
    empty_chats = pd.DataFrame(
        {"user_id": pd.Series(dtype="int64"), "created_at": pd.to_datetime([])}
    )
    empty_alerts = pd.DataFrame(
        {
            "user_id": pd.Series(dtype="int64"),
            "timestamp": pd.to_datetime([]),
            "attack_type": pd.Series(dtype="string"),
        }
    )
    assert detect_anomalous_users(empty_chats, empty_alerts).empty

    chats = pd.DataFrame(
        {"user_id": [3], "created_at": pd.to_datetime(["2026-07-01"])}
    )
    profile = build_user_risk_profile(chats, empty_alerts)
    assert profile.iloc[0]["scored_events"] == 0
    assert pd.isna(profile.iloc[0]["average_risk_score"])
    assert profile.iloc[0]["rule_count"] == 0


def test_rejects_invalid_thresholds() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        AnomalyThresholds(blocked_rate=1.5)
    with pytest.raises(ValueError, match="positive"):
        AnomalyThresholds(high_volume_requests=0)


def test_loads_temporary_exports_without_local_data(tmp_path) -> None:
    (tmp_path / "chat_logs.csv").write_text(
        "user_id,created_at,risk_score,risk_level\n"
        "9,2026-07-01 10:00:00,0,low\n",
        encoding="utf-8",
    )
    (tmp_path / "security_alerts.csv").write_text(
        "user_id,timestamp,attack_type,risk_score,severity\n"
        "9,2026-07-01 11:00:00,prompt_injection,100,high\n",
        encoding="utf-8",
    )
    logs = load_and_clean_logs(tmp_path)
    flagged = detect_anomalous_users(
        logs.chat_logs,
        logs.security_alerts,
        AnomalyThresholds(
            high_volume_requests=2,
            min_requests_for_blocked_rate=2,
            min_blocked_requests=1,
            blocked_rate=0.5,
        ),
    )
    assert flagged["user_id"].tolist() == [9]
    assert flagged.iloc[0]["blocked_rate"] == 0.5
