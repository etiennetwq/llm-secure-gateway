"""Smoke-test the Streamlit page against isolated synthetic CSV files."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_aggregate_metrics(tmp_path, monkeypatch) -> None:
    (tmp_path / "chat_logs.csv").write_text(
        "user_id,created_at,tokens_used,risk_score,risk_level\n"
        "1,2026-07-01 10:00:00,20,0,low\n",
        encoding="utf-8",
    )
    (tmp_path / "security_alerts.csv").write_text(
        "user_id,timestamp,attack_type,risk_score,severity\n"
        "2,2026-07-01 11:00:00,prompt_injection,100,high\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GATEWAY_EXPORT_DIR", str(tmp_path))
    page = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"

    app = AppTest.from_file(page, default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "LLM Security Analytics"
    assert [item.value for item in app.metric[:4]] == ["2", "1", "1", "50.0%"]


def test_dashboard_explains_missing_exports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GATEWAY_EXPORT_DIR", str(tmp_path))
    page = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"

    app = AppTest.from_file(page, default_timeout=10).run()

    assert not app.exception
    assert any("CSV was not found" in item.value for item in app.error)
