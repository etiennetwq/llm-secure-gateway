"""Flag unusual users in cleaned gateway audit logs with explainable rules."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from analyze_logs import LogAnalysisError, build_event_frame, load_and_clean_logs


PROFILE_COLUMNS = [
    "user_id",
    "request_count",
    "blocked_requests",
    "blocked_rate",
    "high_risk_event_count",
    "scored_events",
    "average_risk_score",
    "rule_count",
    "reasons",
]


@dataclass(frozen=True)
class AnomalyThresholds:
    """Explicit local-demo thresholds; these are not trained model parameters."""

    high_volume_requests: int = 100
    min_requests_for_blocked_rate: int = 10
    min_blocked_requests: int = 5
    blocked_rate: float = 0.20
    high_risk_events: int = 15
    min_scored_events: int = 10
    average_risk_score: float = 60.0

    def __post_init__(self) -> None:
        if any(
            value < 1
            for value in (
                self.high_volume_requests,
                self.min_requests_for_blocked_rate,
                self.min_blocked_requests,
                self.high_risk_events,
                self.min_scored_events,
            )
        ):
            raise ValueError("Count thresholds must be positive integers.")
        if not 0 <= self.blocked_rate <= 1:
            raise ValueError("blocked_rate threshold must be between 0 and 1.")
        if self.average_risk_score < 0:
            raise ValueError("average_risk_score threshold cannot be negative.")


def build_user_risk_profile(
    chat_logs: pd.DataFrame,
    security_alerts: pd.DataFrame,
    thresholds: AnomalyThresholds | None = None,
) -> pd.DataFrame:
    """Aggregate logged events by user and record every triggered rule."""

    limits = thresholds or AnomalyThresholds()
    events = build_event_frame(chat_logs, security_alerts)
    if events.empty:
        return pd.DataFrame(columns=PROFILE_COLUMNS)

    events = events.copy()
    events["risk_score"] = pd.to_numeric(events["risk_score"], errors="coerce")
    events["is_high_risk"] = events["is_high_risk"].fillna(False).astype(bool)
    events["has_risk_score"] = events["risk_score"].notna()
    profile = (
        events.groupby("user_id", as_index=False)
        .agg(
            request_count=("user_id", "size"),
            blocked_requests=("blocked_requests", "sum"),
            high_risk_event_count=("is_high_risk", "sum"),
            scored_events=("has_risk_score", "sum"),
            average_risk_score=("risk_score", "mean"),
        )
    )
    profile["blocked_rate"] = profile["blocked_requests"] / profile["request_count"]

    rules = {
        "high_volume": profile["request_count"] >= limits.high_volume_requests,
        "high_blocked_rate": (
            (profile["request_count"] >= limits.min_requests_for_blocked_rate)
            & (profile["blocked_requests"] >= limits.min_blocked_requests)
            & (profile["blocked_rate"] >= limits.blocked_rate)
        ),
        "repeated_high_risk": (
            profile["high_risk_event_count"] >= limits.high_risk_events
        ),
        "high_average_risk": (
            (profile["scored_events"] >= limits.min_scored_events)
            & (profile["average_risk_score"] >= limits.average_risk_score)
        ),
    }
    for name, matches in rules.items():
        profile[name] = matches.fillna(False).astype(bool)
    profile["rule_count"] = profile[list(rules)].sum(axis=1)
    profile["reasons"] = profile.apply(
        lambda row: ", ".join(name for name in rules if row[name]), axis=1
    )
    return profile[PROFILE_COLUMNS].sort_values("user_id").reset_index(drop=True)


def detect_anomalous_users(
    chat_logs: pd.DataFrame,
    security_alerts: pd.DataFrame,
    thresholds: AnomalyThresholds | None = None,
) -> pd.DataFrame:
    """Return flagged users, ordered by triggered rules and blocked rate."""

    profile = build_user_risk_profile(chat_logs, security_alerts, thresholds)
    return (
        profile.loc[profile["rule_count"] > 0]
        .sort_values(
            ["rule_count", "blocked_rate", "request_count", "user_id"],
            ascending=[False, False, False, True],
        )
        .reset_index(drop=True)
    )


def parse_arguments() -> argparse.Namespace:
    """Read paths and the most useful adjustable demo thresholds."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=Path("exports"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--high-volume", type=int, default=100)
    parser.add_argument("--blocked-rate", type=float, default=0.20)
    return parser.parse_args()


def main() -> None:
    """Clean exported logs, flag users, and save a metrics-only CSV."""

    args = parse_arguments()
    output = args.output or args.export_dir / "anomalous_users.csv"
    try:
        thresholds = AnomalyThresholds(
            high_volume_requests=args.high_volume,
            blocked_rate=args.blocked_rate,
        )
        logs = load_and_clean_logs(args.export_dir)
        flagged = detect_anomalous_users(
            logs.chat_logs, logs.security_alerts, thresholds
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        flagged.to_csv(output, index=False, encoding="utf-8")
    except (LogAnalysisError, OSError, ValueError) as error:
        print(f"Anomaly detection failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print(f"Flagged users: {len(flagged)}")
    print(f"Metrics-only output: {output}")
    if logs.warnings:
        print("Data-quality warnings:")
        for warning in logs.warnings:
            print(f"- {warning}")
    print("These are rule-based leads for review, not confirmed attacks.")


if __name__ == "__main__":
    main()
