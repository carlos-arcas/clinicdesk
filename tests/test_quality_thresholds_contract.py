from __future__ import annotations

import json
from pathlib import Path


QUALITY_THRESHOLDS_PATH = Path("scripts/quality_thresholds.json")
WILDCARD_JUSTIFICATION_TOKEN = "ALLOWLIST_WILDCARD_JUSTIFIED"


def _load_allowlist() -> list[dict[str, object]]:
    payload = json.loads(QUALITY_THRESHOLDS_PATH.read_text(encoding="utf-8"))
    return payload.get("allowlist", [])


def test_allowlist_entries_require_reason() -> None:
    missing_reason_paths: list[str] = []
    for entry in _load_allowlist():
        reason = str(entry.get("reason", "")).strip()
        if not reason:
            missing_reason_paths.append(str(entry.get("path", "<missing-path>")))

    assert not missing_reason_paths, (
        "Cada entry de allowlist debe declarar un reason no vacío. "
        f"Entradas inválidas: {missing_reason_paths}"
    )


def test_allowlist_rejects_overly_broad_wildcards_without_justification() -> None:
    broad_paths: list[str] = []
    for entry in _load_allowlist():
        path = str(entry.get("path", "")).strip()
        reason = str(entry.get("reason", ""))
        if path.endswith("/**") and WILDCARD_JUSTIFICATION_TOKEN not in reason:
            broad_paths.append(path)

    assert not broad_paths, (
        "No se permiten patrones allowlist demasiado amplios terminados en '/**' "
        f"sin justificación explícita ({WILDCARD_JUSTIFICATION_TOKEN}). "
        f"Entradas inválidas: {broad_paths}"
    )
