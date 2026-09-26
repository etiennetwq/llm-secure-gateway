"""Small data helpers shared by the dashboard and its tests."""

from __future__ import annotations

from datetime import date

import pandas as pd

from analyze_logs import CleanedLogs


def available_date_range(logs: CleanedLogs) -> tuple[date, date] | None:
    """Return the earliest and latest dates with a valid logged event."""

    dates = pd.concat(
        [logs.chat_logs["created_at"], logs.security_alerts["timestamp"]],
        ignore_index=True,
    ).dropna()
    if dates.empty:
        return None
    return dates.min().date(), dates.max().date()


def filter_logs_by_date(logs: CleanedLogs, start: date, end: date) -> CleanedLogs:
    """Keep both event sources within an inclusive date range."""

    if start > end:
        raise ValueError("Start date must not be after end date.")
    chats = logs.chat_logs.loc[
        logs.chat_logs["created_at"].dt.date.between(start, end)
    ].copy()
    alerts = logs.security_alerts.loc[
        logs.security_alerts["timestamp"].dt.date.between(start, end)
    ].copy()
    return CleanedLogs(chats, alerts, logs.warnings.copy())
