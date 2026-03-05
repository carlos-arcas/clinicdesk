from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "dist",
    "build",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "data",
    ".pytest_cache",
    "logs",
}
MAX_FILE_BYTES = 1_000_000


@dataclass(frozen=True)
class HallazgoSecreto:
    ruta: str
    linea: int | None
    regla: str
    snippet_redactado: str


_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN .* PRIVA" + r"TE KEY-----")),
    ("github_token", re.compile(r"(?:ghp_|github_pat_)[A-Za-z0-9_]{10,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    (
        "api_key_generica",
        re.compile(r"(?i)\b(api[_-]?key|secret|token)\b\s*[:=]\s*[A-Za-z0-9_\-]{16,}"),
    ),
    ("openai_token", re.compile(r"sk-[A-Za-z0-9]{20,}")),
)


def _is_binary(content: bytes) -> bool:
    return b"\x00" in content


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        yield path


def _redact_snippet(line: str, pattern: re.Pattern[str]) -> str:
    redacted = pattern.sub("[REDACTED]", line.strip())
    digest = hashlib.sha256(line.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return f"{redacted[:160]} [sha256:{digest}]"


def scan_repo(root: Path) -> list[HallazgoSecreto]:
    hallazgos: list[HallazgoSecreto] = []
    for file_path in _iter_files(root):
        content = file_path.read_bytes()
        if _is_binary(content):
            continue
        text = content.decode("utf-8", errors="ignore")
        rel_path = str(file_path.relative_to(root))
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule_name, pattern in _RULES:
                if not pattern.search(line):
                    continue
                hallazgos.append(
                    HallazgoSecreto(
                        ruta=rel_path,
                        linea=line_number,
                        regla=rule_name,
                        snippet_redactado=_redact_snippet(line, pattern),
                    )
                )
    return hallazgos


def render_report(hallazgos: list[HallazgoSecreto]) -> str:
    payload = [asdict(item) for item in hallazgos]
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
