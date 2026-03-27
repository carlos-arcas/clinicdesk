from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Iterable

from . import config

_LOGGER = logging.getLogger(__name__)


def iter_repo_files(repo_root: Path | None = None) -> Iterable[Path]:
    root = repo_root or config.REPO_ROOT
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in config.SCAN_EXCLUDE_DIRS for part in rel.parts):
            continue
        yield path


def is_print_allowlisted(file_path: Path, repo_root: Path | None = None) -> bool:
    root = repo_root or config.REPO_ROOT
    rel_path = file_path.relative_to(root)
    return any(rel_path.parts[: len(prefix.parts)] == prefix.parts for prefix in config.PRINT_ALLOWLIST)


def check_no_print_calls(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    offenders: list[Path] = []
    for file_path in iter_repo_files(repo_root=root):
        if file_path.suffix != ".py":
            continue
        if is_print_allowlisted(file_path, repo_root=root):
            continue
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        if any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
            for node in ast.walk(tree)
        ):
            offenders.append(file_path)
    if not offenders:
        return 0
    _LOGGER.error("[quality-gate] ❌ Se detectaron print fuera de allowlist.")
    for file_path in offenders:
        _LOGGER.error("[quality-gate] print encontrado en %s", file_path.relative_to(root))
    return 3


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in config.SECRET_PATTERNS)


def check_secret_patterns(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    offenders: list[Path] = []
    for file_path in iter_repo_files(repo_root=root):
        try:
            if file_path.stat().st_size > config.MAX_SCAN_BYTES:
                continue
            text = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if contains_secret(text):
            offenders.append(file_path.relative_to(root))

    if not offenders:
        return 0
    _LOGGER.error("[quality-gate] ❌ Se detectaron posibles secretos.")
    for path in sorted(offenders):
        _LOGGER.error("[quality-gate] %s: SECRETO DETECTADO", path)
    return 5


def check_forbidden_artifacts(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    offenders: list[Path] = []
    for file_path in iter_repo_files(repo_root=root):
        rel_path = file_path.relative_to(root)
        if rel_path in config.ARTIFACT_ALLOWLIST:
            continue
        if file_path.suffix.lower() in config.ARTIFACT_SUFFIXES:
            offenders.append(rel_path)

    if not offenders:
        return 0
    _LOGGER.error("[quality-gate] ❌ Se detectaron artefactos prohibidos.")
    for path in sorted(offenders):
        _LOGGER.error("[quality-gate] Artefacto prohibido: %s", path)
    return 4
