"""Date filtering tests that do not need a running Streamlit server."""

from datetime import date

import pandas as pd
import pytest

from analyze_logs import CleanedLogs, calculate_metrics
from dashboard.data import available_date_range, filter_logs_by_date


def sample_logs() -> CleanedLogs:
    """Build two clean event streams across two dates."""

    chats = pd.DataFrame(
        {
            "user_id": [1, 2],
            "created_at": pd.to_datetime(["2026-07-01", "2026-07-02"]),
            "risk_score": [0, 50],
            "risk_level": ["low", "medium"],
        }
    )
    alerts = pd.DataFrame(
        {
            "user_id": [2],
            "timestamp": pd.to_datetime(["2026-07-02"]),
            "attack_type": ["prompt_injection"],
            "risk_score": [100],
            "severity": ["high"],
        }
    )
    return CleanedLogs(chats, alerts, [])


def test_date_filter_is_inclusive_and_preserves_original() -> None:
    logs = sample_logs()
    assert available_date_range(logs) == (date(2026, 7, 1), date(2026, 7, 2))
    filtered = filter_logs_by_date(logs, date(2026, 7, 2), date(2026, 7, 2))
    assert calculate_metrics(filtered.chat_logs, filtered.security_alerts)["total_requests"] == 2
    assert len(logs.chat_logs) == 2


def test_empty_range_and_reversed_dates() -> None:
    logs = sample_logs()
    filtered = filter_logs_by_date(logs, date(2026, 7, 3), date(2026, 7, 3))
    assert available_date_range(filtered) is None
    with pytest.raises(ValueError, match="Start date"):
        filter_logs_by_date(logs, date(2026, 7, 2), date(2026, 7, 1))
