"""Clean exported gateway logs and calculate security analytics metrics."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_EXPORT_DIR = Path("exports")
CHAT_LOG_FILENAME = "chat_logs.csv"
SECURITY_ALERT_FILENAME = "security_alerts.csv"

CHAT_REQUIRED_COLUMNS = {"user_id", "created_at"}
ALERT_REQUIRED_COLUMNS = {"user_id", "timestamp", "attack_type"}


class LogAnalysisError(ValueError):
    """Raised when exported log data cannot be safely analyzed."""


@dataclass
class CleanedLogs:
    """Cleaned data frames and warnings produced during analysis."""

    chat_logs: pd.DataFrame
    security_alerts: pd.DataFrame
    warnings: list[str]


def read_log_csv(path: Path, source_name: str) -> pd.DataFrame:
    """Read one UTF-8 CSV file and retain raw values as nullable strings."""

    if not path.is_file():
        raise LogAnalysisError(
            f"{source_name} CSV was not found: {path}. "
            "Run 'python export_logs.py' first."
        )

    try:
        return pd.read_csv(path, dtype="string", keep_default_na=False)
    except pd.errors.EmptyDataError as error:
        raise LogAnalysisError(
            f"{source_name} CSV is empty and has no header row: {path}."
        ) from error
    except UnicodeDecodeError as error:
        raise LogAnalysisError(
            f"{source_name} CSV is not valid UTF-8: {path}."
        ) from error
    except pd.errors.ParserError as error:
        raise LogAnalysisError(
            f"{source_name} CSV could not be parsed: {path}."
        ) from error


def require_columns(
    frame: pd.DataFrame,
    required_columns: set[str],
    source_name: str
) -> None:
    """Raise a clear error when a CSV misses fields required for analysis."""

    missing_columns = sorted(required_columns - set(frame.columns))

    if missing_columns:
        raise LogAnalysisError(
            f"{source_name} CSV is missing required columns: "
            + ", ".join(missing_columns)
        )


def normalize_text_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim text values and convert empty strings to pandas missing values."""

    cleaned = frame.copy()

    for column in cleaned.columns:
        if pd.api.types.is_string_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].str.strip().replace("", pd.NA)

    return cleaned


def coerce_numeric_column(
    frame: pd.DataFrame,
    column: str,
    source_name: str,
    warnings: list[str]
) -> pd.DataFrame:
    """Convert an optional numeric column and report malformed values."""

    if column not in frame.columns:
        warnings.append(
            f"{source_name}: optional numeric column '{column}' is missing."
        )
        return frame

    converted = pd.to_numeric(frame[column], errors="coerce")
    invalid_count = (frame[column].notna() & converted.isna()).sum()

    if invalid_count:
        warnings.append(
            f"{source_name}: {invalid_count} invalid '{column}' value(s) were "
            "treated as missing."
        )

    frame[column] = converted
    return frame


def warn_missing_optional_column(
    frame: pd.DataFrame,
    column: str,
    source_name: str,
    warnings: list[str],
    substitute_description: str
) -> None:
    """Explain the impact when an optional metric field is unavailable."""

    if column not in frame.columns:
        warnings.append(
            f"{source_name}: optional column '{column}' is missing; "
            f"{substitute_description}"
        )


def clean_chat_logs(frame: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    """Clean chat log records and remove rows without valid user IDs or dates."""

    require_columns(frame, CHAT_REQUIRED_COLUMNS, "chat_logs")
    cleaned = normalize_text_columns(frame)
    warn_missing_optional_column(
        cleaned,
        "risk_level",
        "chat_logs",
        warnings,
        "risk-level distribution excludes successful chat rows."
    )
    cleaned = coerce_numeric_column(cleaned, "user_id", "chat_logs", warnings)
    cleaned = coerce_numeric_column(cleaned, "tokens_used", "chat_logs", warnings)
    cleaned = coerce_numeric_column(cleaned, "risk_score", "chat_logs", warnings)

    parsed_dates = pd.to_datetime(cleaned["created_at"], errors="coerce")
    invalid_dates = (cleaned["created_at"].notna() & parsed_dates.isna()).sum()

    if invalid_dates:
        warnings.append(
            f"chat_logs: {invalid_dates} invalid 'created_at' value(s) were removed."
        )

    cleaned["created_at"] = parsed_dates
    valid_rows = cleaned["user_id"].notna() & cleaned["created_at"].notna()
    removed_rows = (~valid_rows).sum()

    if removed_rows:
        warnings.append(
            f"chat_logs: removed {removed_rows} row(s) without a valid user_id and "
            "created_at timestamp."
        )

    return cleaned.loc[valid_rows].copy()


def clean_security_alerts(frame: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    """Clean security alerts and remove rows without valid audit identifiers."""

    require_columns(frame, ALERT_REQUIRED_COLUMNS, "security_alerts")
    cleaned = normalize_text_columns(frame)
    warn_missing_optional_column(
        cleaned,
        "severity",
        "security_alerts",
        warnings,
        "blocked alerts are classified as high risk based on alert status."
    )
    cleaned = coerce_numeric_column(
        cleaned,
        "user_id",
        "security_alerts",
        warnings
    )
    cleaned = coerce_numeric_column(
        cleaned,
        "risk_score",
        "security_alerts",
        warnings
    )

    parsed_dates = pd.to_datetime(cleaned["timestamp"], errors="coerce")
    invalid_dates = (cleaned["timestamp"].notna() & parsed_dates.isna()).sum()

    if invalid_dates:
        warnings.append(
            "security_alerts: "
            f"{invalid_dates} invalid 'timestamp' value(s) were removed."
        )

    cleaned["timestamp"] = parsed_dates
    valid_rows = (
        cleaned["user_id"].notna()
        & cleaned["timestamp"].notna()
        & cleaned["attack_type"].notna()
    )
    removed_rows = (~valid_rows).sum()

    if removed_rows:
        warnings.append(
            "security_alerts: removed "
            f"{removed_rows} row(s) without a valid user_id, timestamp, or attack_type."
        )

    return cleaned.loc[valid_rows].copy()


def load_and_clean_logs(export_dir: Path) -> CleanedLogs:
    """Load both exported CSV files and clean them for metric calculations."""

    warnings: list[str] = []
    chat_frame = read_log_csv(export_dir / CHAT_LOG_FILENAME, "chat_logs")
    alert_frame = read_log_csv(
        export_dir / SECURITY_ALERT_FILENAME,
        "security_alerts"
    )

    return CleanedLogs(
        chat_logs=clean_chat_logs(chat_frame, warnings),
        security_alerts=clean_security_alerts(alert_frame, warnings),
        warnings=warnings
    )


def build_event_frame(
    chat_logs: pd.DataFrame,
    security_alerts: pd.DataFrame
) -> pd.DataFrame:
    """Combine successful chats and blocked alerts into one event-level frame."""

    chat_events = pd.DataFrame(
        {
            "user_id": chat_logs["user_id"],
            "event_date": chat_logs["created_at"].dt.normalize(),
            "risk_score": chat_logs.get(
                "risk_score",
                pd.Series(pd.NA, index=chat_logs.index, dtype="Float64")
            ),
            "risk_level": chat_logs.get(
                "risk_level",
                pd.Series(pd.NA, index=chat_logs.index, dtype="string")
            ),
            "successful_requests": 1,
            "blocked_requests": 0,
            "is_high_risk": chat_logs.get(
                "risk_level",
                pd.Series(pd.NA, index=chat_logs.index, dtype="string")
            ).eq("high")
        }
    )

    alert_events = pd.DataFrame(
        {
            "user_id": security_alerts["user_id"],
            "event_date": security_alerts["timestamp"].dt.normalize(),
            "risk_score": security_alerts.get(
                "risk_score",
                pd.Series(pd.NA, index=security_alerts.index, dtype="Float64")
            ),
            "risk_level": security_alerts.get(
                "severity",
                pd.Series("high", index=security_alerts.index, dtype="string")
            ).fillna("high"),
            "successful_requests": 0,
            "blocked_requests": 1,
            "is_high_risk": True
        }
    )

    return pd.concat([chat_events, alert_events], ignore_index=True)


def sorted_user_counts(frame: pd.DataFrame, value_name: str) -> pd.DataFrame:
    """Count events by user, keeping deterministic ordering for tied values."""

    if frame.empty:
        return pd.DataFrame(columns=["user_id", value_name])

    return (
        frame.groupby("user_id", dropna=False)
        .size()
        .rename(value_name)
        .reset_index()
        .sort_values([value_name, "user_id"], ascending=[False, True])
        .reset_index(drop=True)
    )


def calculate_metrics(
    chat_logs: pd.DataFrame,
    security_alerts: pd.DataFrame
) -> dict[str, Any]:
    """Calculate aggregate, user-level, and daily security analytics metrics."""

    events = build_event_frame(chat_logs, security_alerts)
    successful_requests = len(chat_logs)
    blocked_requests = len(security_alerts)
    total_requests = successful_requests + blocked_requests
    blocked_rate = (
        blocked_requests / total_requests
        if total_requests
        else None
    )

    risk_level_distribution = (
        events["risk_level"].dropna().value_counts().sort_index()
    )
    attack_type_distribution = (
        security_alerts["attack_type"].dropna().value_counts().sort_index()
    )

    average_token_usage = (
        chat_logs["tokens_used"].dropna().mean()
        if "tokens_used" in chat_logs.columns
        else None
    )
    average_token_usage = (
        float(average_token_usage)
        if average_token_usage is not None and pd.notna(average_token_usage)
        else None
    )

    user_request_ranking = sorted_user_counts(events, "request_count")
    high_risk_user_ranking = sorted_user_counts(
        events.loc[events["is_high_risk"]],
        "high_risk_event_count"
    )

    risk_score_events = events.dropna(subset=["risk_score"])
    average_risk_score_by_user = (
        risk_score_events.groupby("user_id", as_index=False)
        .agg(average_risk_score=("risk_score", "mean"))
        .sort_values(["average_risk_score", "user_id"], ascending=[False, True])
        .reset_index(drop=True)
    )

    if events.empty:
        daily_metrics = pd.DataFrame(
            columns=[
                "date",
                "total_requests",
                "successful_requests",
                "blocked_requests",
                "blocked_rate",
                "average_risk_score"
            ]
        )
    else:
        daily_metrics = (
            events.groupby("event_date", as_index=False)
            .agg(
                total_requests=("user_id", "size"),
                successful_requests=("successful_requests", "sum"),
                blocked_requests=("blocked_requests", "sum"),
                average_risk_score=("risk_score", "mean")
            )
            .rename(columns={"event_date": "date"})
            .sort_values("date")
            .reset_index(drop=True)
        )
        daily_metrics["blocked_rate"] = (
            daily_metrics["blocked_requests"] / daily_metrics["total_requests"]
        )
        daily_metrics = daily_metrics[
            [
                "date",
                "total_requests",
                "successful_requests",
                "blocked_requests",
                "blocked_rate",
                "average_risk_score"
            ]
        ]

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "blocked_requests": blocked_requests,
        "blocked_rate": blocked_rate,
        "risk_level_distribution": risk_level_distribution,
        "attack_type_distribution": attack_type_distribution,
        "average_token_usage": average_token_usage,
        "user_request_ranking": user_request_ranking,
        "high_risk_user_ranking": high_risk_user_ranking,
        "average_risk_score_by_user": average_risk_score_by_user,
        "daily_metrics": daily_metrics
    }


def print_series(title: str, series: pd.Series) -> None:
    """Print one distribution without hiding an empty result."""

    print(f"\n{title}")

    if series.empty:
        print("  No valid data available.")
        return

    print(series.to_string())


def print_table(title: str, frame: pd.DataFrame, limit: int = 10) -> None:
    """Print a bounded table for command-line analytics output."""

    print(f"\n{title}")

    if frame.empty:
        print("  No valid data available.")
        return

    print(frame.head(limit).to_string(index=False))


def print_metrics(metrics: dict[str, Any], warnings: list[str]) -> None:
    """Print the required metrics and all data-quality warnings."""

    blocked_rate = metrics["blocked_rate"]
    rate_text = "N/A" if blocked_rate is None else f"{blocked_rate:.2%}"
    average_tokens = metrics["average_token_usage"]
    token_text = "N/A" if average_tokens is None else f"{average_tokens:.2f}"

    print("Security Log Analysis Summary")
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Successful requests: {metrics['successful_requests']}")
    print(f"Blocked requests: {metrics['blocked_requests']}")
    print(f"Blocked rate: {rate_text}")
    print(f"Average token usage: {token_text}")

    print_series("Risk level distribution:", metrics["risk_level_distribution"])
    print_series("Attack type distribution:", metrics["attack_type_distribution"])
    print_table("User request ranking:", metrics["user_request_ranking"])
    print_table("High-risk user ranking:", metrics["high_risk_user_ranking"])
    print_table(
        "Average risk score by user:",
        metrics["average_risk_score_by_user"]
    )
    print_table("Daily request and risk metrics:", metrics["daily_metrics"], 31)

    if warnings:
        print("\nData-quality warnings:")
        for warning in warnings:
            print(f"- {warning}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the analysis script."""

    parser = argparse.ArgumentParser(
        description="Clean exported LLM gateway logs and calculate statistics."
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=DEFAULT_EXPORT_DIR,
        help="Directory containing exported CSV files. Default: exports"
    )
    return parser.parse_args()


def main() -> None:
    """Run CSV analysis from the project root and print the results."""

    args = parse_arguments()

    try:
        cleaned_logs = load_and_clean_logs(args.export_dir)
        metrics = calculate_metrics(
            cleaned_logs.chat_logs,
            cleaned_logs.security_alerts
        )
        print_metrics(metrics, cleaned_logs.warnings)
    except LogAnalysisError as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
