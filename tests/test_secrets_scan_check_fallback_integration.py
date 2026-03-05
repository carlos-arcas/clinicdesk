from __future__ import annotations

from scripts.quality_gate_components import secrets_scan_check


def test_run_secrets_scan_fallback_generates_report_and_fails_with_findings(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "docs" / "secrets_scan_report.txt"
    (tmp_path / "app.env").write_text("TOKEN=" + "sk" + "-" + "ABCDEFGHIJKLMNOPQRSTUV" + "\n", encoding="utf-8")

    monkeypatch.setattr(secrets_scan_check.shutil, "which", lambda _: None)

    result = secrets_scan_check.run_secrets_scan(report_path=report_path, repo_root=tmp_path)

    assert result == 7
    assert report_path.exists()
    contenido = report_path.read_text(encoding="utf-8")
    assert "openai_token" in contenido
    assert "sk" + "-" + "ABCDEFGHIJKLMNOPQRSTUV" not in contenido


def test_run_secrets_scan_fallback_passes_without_findings(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "docs" / "secrets_scan_report.txt"
    (tmp_path / "README.md").write_text("texto sin secretos\n", encoding="utf-8")

    monkeypatch.setattr(secrets_scan_check.shutil, "which", lambda _: None)

    result = secrets_scan_check.run_secrets_scan(report_path=report_path, repo_root=tmp_path)

    assert result == 0
    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8").strip() == "[]"
