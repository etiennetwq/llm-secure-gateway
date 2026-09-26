"""End-to-end analytics check using only synthetic temporary data."""

import init_db
from analyze_logs import calculate_metrics, load_and_clean_logs
from detect_anomalies import detect_anomalous_users
from export_logs import export_logs
from generate_demo_logs import generate_demo_logs


def test_synthetic_database_to_csv_to_analytics(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "demo.db"
    export_dir = tmp_path / "exports"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    init_db.init_database()

    generate_demo_logs(
        database_path=database_path,
        user_count=30,
        chat_log_count=1000,
        alert_count=120,
        days=30,
        seed=42,
        reset_demo=True,
    )
    assert export_logs(database_path, export_dir) == {
        "chat_logs": 1000,
        "security_alerts": 120,
    }

    logs = load_and_clean_logs(export_dir)
    metrics = calculate_metrics(logs.chat_logs, logs.security_alerts)
    flagged = detect_anomalous_users(logs.chat_logs, logs.security_alerts)

    assert metrics["total_requests"] == 1120
    assert metrics["blocked_rate"] == 120 / 1120
    assert not metrics["daily_metrics"].empty
    assert not flagged.empty
    assert flagged["reasons"].str.len().gt(0).all()
