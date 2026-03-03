from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts import quality_gate


def test_contains_secret_detects_high_confidence_patterns() -> None:
    aws_access_key = "AKIA" + "1234567890ABCDEF"
    assert quality_gate._contains_secret(f"aws_key={aws_access_key}")
    api_key_value = "abcdEFGH" + "1234" + "token"
    assert quality_gate._contains_secret(f'api_key = "{api_key_value}"')


def test_contains_secret_ignores_safe_text() -> None:
    assert not quality_gate._contains_secret("this is normal documentation text")


def test_forbidden_artifact_fails_without_allowlist(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "dump.db").write_text("sqlite", encoding="utf-8")

    monkeypatch.setattr(quality_gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(quality_gate, "ARTIFACT_ALLOWLIST", set())

    assert quality_gate._check_forbidden_artifacts() == 4


def test_secret_pattern_check_reports_file_without_printing_match(tmp_path: Path, monkeypatch) -> None:
    secret_file = tmp_path / "config.env"
    token_value = "abcd1234" + "abcd1234"
    secret_file.write_text(f"TOKEN={token_value}", encoding="utf-8")

    monkeypatch.setattr(quality_gate, "REPO_ROOT", tmp_path)

    assert quality_gate._check_secret_patterns() == 5


def test_run_pip_audit_applies_allowlist_ids(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "pip_audit_report.txt"
    allowlist_path = tmp_path / "pip_audit_allowlist.json"
    allowlist_path.write_text(
        json.dumps(
            {
                "vulnerabilidades_permitidas": [
                    {"id": "CVE-2024-0001", "motivo": "falso positivo reproducible"},
                    {"id": "GHSA-xxxx-yyyy-zzzz", "motivo": "pendiente upstream"},
                ]
            }
        ),
        encoding="utf-8",
    )

    def fake_run(command, **kwargs):
        report_path.write_text("vuln report", encoding="utf-8")
        salida = "Found 2 known vulnerabilities: CVE-2024-0001 GHSA-xxxx-yyyy-zzzz"
        return subprocess.CompletedProcess(command, 1, salida, "")

    monkeypatch.setattr(quality_gate, "PIP_AUDIT_REPORT_PATH", report_path)
    monkeypatch.setattr(quality_gate, "PIP_AUDIT_ALLOWLIST_PATH", allowlist_path)
    monkeypatch.setattr(quality_gate.subprocess, "run", fake_run)

    assert quality_gate._run_pip_audit() == 0


def test_run_pip_audit_missing_module_writes_report_and_fails(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "pip_audit_report.txt"

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "/usr/bin/python: No module named pip_audit")

    monkeypatch.setattr(quality_gate, "PIP_AUDIT_REPORT_PATH", report_path)
    monkeypatch.setattr(quality_gate.subprocess, "run", fake_run)

    assert quality_gate._run_pip_audit() != 0
    assert "Instala dependencias dev: pip install -r requirements-dev.txt" in report_path.read_text(encoding="utf-8")


def test_run_pip_audit_fails_when_non_allowlisted_vulnerability_remains(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "pip_audit_report.txt"
    allowlist_path = tmp_path / "pip_audit_allowlist.json"
    allowlist_path.write_text(
        json.dumps({"vulnerabilidades_permitidas": [{"id": "CVE-2024-0001", "motivo": "temporal"}]}),
        encoding="utf-8",
    )

    def fake_run(command, **kwargs):
        report_path.write_text("raw output", encoding="utf-8")
        salida = "Found vulnerabilities CVE-2024-0001 GHSA-1111-2222-3333"
        return subprocess.CompletedProcess(command, 1, salida, "")

    monkeypatch.setattr(quality_gate, "PIP_AUDIT_REPORT_PATH", report_path)
    monkeypatch.setattr(quality_gate, "PIP_AUDIT_ALLOWLIST_PATH", allowlist_path)
    monkeypatch.setattr(quality_gate.subprocess, "run", fake_run)

    assert quality_gate._run_pip_audit() == 6
    contenido = report_path.read_text(encoding="utf-8")
    assert "raw output" in contenido
    assert "GHSA-1111-2222-3333" in contenido


def test_run_secrets_scan_fails_when_tool_missing(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "secrets_scan_report.txt"

    monkeypatch.setattr(quality_gate, "SECRETS_SCAN_REPORT_PATH", report_path)
    monkeypatch.setattr(quality_gate, "_find_command_path", lambda _: None)

    assert quality_gate._run_secrets_scan() == 7
    assert "No se encontró gitleaks" in report_path.read_text(encoding="utf-8")


def test_pii_logging_guardrail_detects_sensitive_message(tmp_path: Path, monkeypatch) -> None:
    source_file = tmp_path / "module.py"
    source_file.write_text('logger.info("error con email del paciente")\n', encoding="utf-8")

    monkeypatch.setattr(quality_gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(quality_gate, "PII_LOGGING_ALLOWLIST_PATH", tmp_path / "allowlist.json")

    assert quality_gate._check_pii_logging_guardrail() == 8
