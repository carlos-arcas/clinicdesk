from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

from . import config

_LOGGER = logging.getLogger(__name__)


def load_pii_allowlist(allowlist_path: Path) -> dict[str, str]:
    if not allowlist_path.exists():
        return {}
    try:
        payload = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _LOGGER.error("[quality-gate] ❌ Allowlist de PII inválida: %s", exc)
        return {}
    entries = payload.get("entradas", [])
    return {
        str(entry.get("clave", "")).strip(): str(entry.get("motivo", "")).strip()
        for entry in entries
        if str(entry.get("clave", "")).strip() and str(entry.get("motivo", "")).strip()
    }


def extract_string_literals(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        return [
            value.value for value in node.values if isinstance(value, ast.Constant) and isinstance(value.value, str)
        ]
    return []


def _iter_python_files(repo_root: Path):
    for file_path in repo_root.rglob("*.py"):
        rel = file_path.relative_to(repo_root)
        if rel.parts and rel.parts[0] in config.PII_GUARDRAIL_EXCLUDED_ROOTS:
            continue
        if "__pycache__" in rel.parts:
            continue
        yield file_path, rel


def _check_logging_call(node: ast.Call, rel_path: Path, allowlist: dict[str, str]) -> list[str]:
    offenders: list[str] = []
    if not isinstance(node.func, ast.Attribute) or node.func.attr not in config.PII_LOGGING_METHODS:
        return offenders
    for argument in node.args:
        for literal in extract_string_literals(argument):
            matched = [token for token in config.PII_TOKENS if token in literal.lower()]
            if not matched:
                continue
            key = f"{rel_path}:{node.lineno}:{','.join(matched)}"
            if key not in allowlist:
                offenders.append(key)
    return offenders


def _scan_file_for_offenders(file_path: Path, rel_path: Path, allowlist: dict[str, str]) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            offenders.extend(_check_logging_call(node, rel_path, allowlist))
    return offenders


def check_pii_logging_guardrail(repo_root: Path | None = None, allowlist_path: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    allowlist = load_pii_allowlist(allowlist_path or config.PII_LOGGING_ALLOWLIST_PATH)
    offenders: list[str] = []
    for file_path, rel_path in _iter_python_files(root):
        offenders.extend(_scan_file_for_offenders(file_path, rel_path, allowlist))
    if not offenders:
        return 0
    _LOGGER.error("[quality-gate] ❌ Guardrail PII/logging detectó mensajes hardcodeados sensibles.")
    for offender in sorted(offenders):
        _LOGGER.error("[quality-gate] %s", offender)
    return 8
