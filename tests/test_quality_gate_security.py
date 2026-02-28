from __future__ import annotations

from pathlib import Path

from scripts import quality_gate


def test_contains_secret_detects_high_confidence_patterns() -> None:
    assert quality_gate._contains_secret("aws_key=AKIA1234567890ABCDEF")
    assert quality_gate._contains_secret('api_key = "abcdEFGH1234token"')


def test_contains_secret_ignores_safe_text() -> None:
    assert not quality_gate._contains_secret("this is normal documentation text")


def test_forbidden_artifact_fails_without_allowlist(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "dump.db").write_text("sqlite", encoding="utf-8")

    monkeypatch.setattr(quality_gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(quality_gate, "ARTIFACT_ALLOWLIST", set())

    assert quality_gate._check_forbidden_artifacts() == 4


def test_secret_pattern_check_reports_file_without_printing_match(tmp_path: Path, monkeypatch) -> None:
    secret_file = tmp_path / "config.env"
    secret_file.write_text("TOKEN=abcd1234abcd1234", encoding="utf-8")

    monkeypatch.setattr(quality_gate, "REPO_ROOT", tmp_path)

    assert quality_gate._check_secret_patterns() == 5
