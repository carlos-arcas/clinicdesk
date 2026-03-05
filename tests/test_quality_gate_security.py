from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from scripts.quality_gate_components import basic_repo_checks, pii_guardrail, pip_audit_check, secrets_scan_check


def test_contains_secret_detects_high_confidence_patterns() -> None:
    aws_access_key = "AKIA" + "1234567890ABCDEF"
    assert basic_repo_checks.contains_secret(f"aws_key={aws_access_key}")
    api_key_value = "abcdEFGH" + "1234" + "token"
    assert basic_repo_checks.contains_secret(f'api_key = "{api_key_value}"')


def test_contains_secret_ignores_safe_text() -> None:
    assert not basic_repo_checks.contains_secret("this is normal documentation text")


def test_forbidden_artifact_fails_without_allowlist(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "dump.db").write_text("sqlite", encoding="utf-8")

    monkeypatch.setattr(basic_repo_checks.config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(basic_repo_checks.config, "ARTIFACT_ALLOWLIST", set())

    assert basic_repo_checks.check_forbidden_artifacts() == 4


def test_secret_pattern_check_reports_file_without_printing_match(tmp_path: Path, monkeypatch) -> None:
    secret_file = tmp_path / "config.env"
    token_value = "abcd1234" + "abcd1234"
    secret_file.write_text(f"TOKEN={token_value}", encoding="utf-8")

    monkeypatch.setattr(basic_repo_checks.config, "REPO_ROOT", tmp_path)

    assert basic_repo_checks.check_secret_patterns() == 5


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

    monkeypatch.setattr(pip_audit_check.config, "PIP_AUDIT_REPORT_PATH", report_path)
    monkeypatch.setattr(pip_audit_check.config, "PIP_AUDIT_ALLOWLIST_PATH", allowlist_path)
    monkeypatch.setattr(pip_audit_check.subprocess, "run", fake_run)

    assert pip_audit_check.run_pip_audit() == 0


def test_run_pip_audit_missing_module_writes_report_and_fails(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "pip_audit_report.txt"

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "/usr/bin/python: No module named pip_audit")

    monkeypatch.setattr(pip_audit_check.config, "PIP_AUDIT_REPORT_PATH", report_path)
    monkeypatch.setattr(pip_audit_check.subprocess, "run", fake_run)

    assert pip_audit_check.run_pip_audit() != 0
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

    monkeypatch.setattr(pip_audit_check.config, "PIP_AUDIT_REPORT_PATH", report_path)
    monkeypatch.setattr(pip_audit_check.config, "PIP_AUDIT_ALLOWLIST_PATH", allowlist_path)
    monkeypatch.setattr(pip_audit_check.subprocess, "run", fake_run)

    assert pip_audit_check.run_pip_audit() == 6
    contenido = report_path.read_text(encoding="utf-8")
    assert "raw output" in contenido
    assert "GHSA-1111-2222-3333" in contenido


def test_run_secrets_scan_uses_gitleaks_config_file(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "secrets_scan_report.txt"
    observed_command: list[str] = []

    def fake_run(command, **kwargs):
        observed_command.extend(command)
        report_path.write_text("[]\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(secrets_scan_check.config, "SECRETS_SCAN_REPORT_PATH", report_path)
    monkeypatch.setattr(secrets_scan_check, "find_command_path", lambda _: "gitleaks")
    monkeypatch.setattr(secrets_scan_check.subprocess, "run", fake_run)

    assert secrets_scan_check.run_secrets_scan() == 0
    assert "--config" in observed_command
    config_index = observed_command.index("--config")
    assert observed_command[config_index + 1] == ".gitleaks.toml"


def test_run_secrets_scan_uses_fallback_when_tool_missing(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "secrets_scan_report.txt"
    (tmp_path / "README.md").write_text("sin secretos\n", encoding="utf-8")

    monkeypatch.setattr(secrets_scan_check.config, "SECRETS_SCAN_REPORT_PATH", report_path)
    monkeypatch.setattr(secrets_scan_check, "find_command_path", lambda _: None)

    assert secrets_scan_check.run_secrets_scan(repo_root=tmp_path) == 0
    assert report_path.read_text(encoding="utf-8").strip() == "[]"


def test_pii_logging_guardrail_detects_sensitive_message(tmp_path: Path, monkeypatch) -> None:
    source_file = tmp_path / "module.py"
    source_file.write_text('logger.info("error con email del paciente")\n', encoding="utf-8")

    monkeypatch.setattr(basic_repo_checks.config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pii_guardrail.config, "PII_LOGGING_ALLOWLIST_PATH", tmp_path / "allowlist.json")

    assert pii_guardrail.check_pii_logging_guardrail() == 8


def test_pii_logging_guardrail_ignores_tests_folder(tmp_path: Path, monkeypatch) -> None:
    tests_file = tmp_path / "tests" / "test_any.py"
    tests_file.parent.mkdir(parents=True, exist_ok=True)
    tests_file.write_text('logger.info("mensaje con email paciente")\n', encoding="utf-8")

    monkeypatch.setattr(basic_repo_checks.config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pii_guardrail.config, "PII_LOGGING_ALLOWLIST_PATH", tmp_path / "allowlist.json")

    assert pii_guardrail.check_pii_logging_guardrail() == 0


def test_run_pip_audit_resets_report_before_execution(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "pip_audit_report.txt"
    report_path.write_text("RESTO RUN ANTERIOR", encoding="utf-8")
    report_seen_during_run: list[str] = []

    def fake_run(command, **kwargs):
        report_seen_during_run.append(report_path.read_text(encoding="utf-8"))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(pip_audit_check.config, "PIP_AUDIT_REPORT_PATH", report_path)
    monkeypatch.setattr(pip_audit_check.subprocess, "run", fake_run)

    assert pip_audit_check.run_pip_audit() == 0
    assert report_seen_during_run == [""]


def test_run_secrets_scan_resets_report_and_keeps_valid_json(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "secrets_scan_report.txt"
    report_path.write_text("resto no json", encoding="utf-8")
    report_seen_during_run: list[str] = []

    def fake_run(command, **kwargs):
        report_seen_during_run.append(report_path.read_text(encoding="utf-8"))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(secrets_scan_check.config, "SECRETS_SCAN_REPORT_PATH", report_path)
    monkeypatch.setattr(secrets_scan_check, "find_command_path", lambda _: "gitleaks")
    monkeypatch.setattr(secrets_scan_check.subprocess, "run", fake_run)

    assert secrets_scan_check.run_secrets_scan() == 0
    assert report_seen_during_run == ["[]\n"]
    assert json.loads(report_path.read_text(encoding="utf-8")) == []


def test_run_secrets_scan_logs_only_method_and_count_without_secret(tmp_path: Path, monkeypatch, caplog) -> None:
    report_path = tmp_path / "docs" / "secrets_scan_report.txt"
    secret_value = "sk" + "-" + "ABCDEFGHIJKLMNOPQRSTUV"
    (tmp_path / "token.env").write_text(f"TOKEN={secret_value}\n", encoding="utf-8")

    monkeypatch.setattr(secrets_scan_check, "find_command_path", lambda _: None)

    with caplog.at_level(logging.INFO):
        assert secrets_scan_check.run_secrets_scan(report_path=report_path, repo_root=tmp_path) == 7

    assert secret_value not in caplog.text
    assert "metodo=fallback" in caplog.text
    assert "hallazgos=" in caplog.text
