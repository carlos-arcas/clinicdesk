from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if Path.cwd() != REPO_ROOT:
    os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CORE_PATHS = [
    REPO_ROOT / "clinicdesk" / "app" / "domain" / "enums.py",
    REPO_ROOT / "clinicdesk" / "app" / "domain" / "exceptions.py",
    REPO_ROOT / "clinicdesk" / "app" / "application" / "usecases" / "crear_cita.py",
    REPO_ROOT / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "repos_citas.py",
    REPO_ROOT / "clinicdesk" / "app" / "queries" / "citas_queries.py",
]
MIN_COVERAGE = 85.0
COVERAGE_XML_PATH = REPO_ROOT / "docs" / "coverage.xml"
PRINT_ALLOWLIST = {Path("tests")}
ARTIFACT_SUFFIXES = {".zip", ".db", ".sqlite", ".sqlite3", ".dump", ".bak", ".sqlitedb"}
ARTIFACT_ALLOWLIST = {Path("clinicdesk.zip")}
SCAN_EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "logs"}
MAX_SCAN_BYTES = 1_000_000
PIP_AUDIT_REPORT_PATH = REPO_ROOT / "docs" / "pip_audit_report.txt"
PIP_AUDIT_ALLOWLIST_PATH = REPO_ROOT / "docs" / "pip_audit_allowlist.json"
SECRETS_SCAN_REPORT_PATH = REPO_ROOT / "docs" / "secrets_scan_report.txt"
PII_LOGGING_ALLOWLIST_PATH = REPO_ROOT / "docs" / "pii_logging_allowlist.json"
MYPY_SCOPE_PATH = REPO_ROOT / "scripts" / "mypy_scope.txt"
MYPY_REPORT_PATH = REPO_ROOT / "docs" / "mypy_report.txt"
PII_GUARDRAIL_EXCLUDED_ROOTS = {"tests", "docs", "scripts"}
PII_TOKENS = ("dni", "nif", "email", "telefono", "direccion", "historia_clinica")
PII_LOGGING_METHODS = {"debug", "info", "warning", "error", "critical", "exception", "log"}
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?(?=[A-Za-z0-9_\-+/=]*\d)[A-Za-z0-9_\-+/=]{12,}"
    ),
)
MENSAJE_INSTALAR_DEPS_DEV = "Instala dependencias dev: pip install -r requirements-dev.txt"
