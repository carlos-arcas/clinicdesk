from __future__ import annotations

import os
from pathlib import Path

_EXTENSIONES_DB_PERMITIDAS = frozenset({".db", ".sqlite", ".sqlite3"})
_ENV_SAFE_ROOTS = "CLINICDESK_SAFE_DB_ROOTS"
_DEFAULT_SAFE_ROOTS = "data;tmp"


def es_ruta_db_segura_para_reset(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    if resolved == Path("/"):
        return False
    if resolved == Path.home().resolve():
        return False
    if resolved.suffix.lower() not in _EXTENSIONES_DB_PERMITIDAS:
        return False
    if _contiene_palabra_segura(resolved):
        return True
    return any(_is_inside_root(resolved, raiz) for raiz in _safe_roots())


def _safe_roots() -> tuple[Path, ...]:
    raw = os.getenv(_ENV_SAFE_ROOTS, _DEFAULT_SAFE_ROOTS)
    roots: list[Path] = []
    for token in (item.strip() for item in raw.split(";")):
        if not token:
            continue
        candidate = Path(token)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        roots.append(candidate.resolve())
    return tuple(roots)


def _contiene_palabra_segura(path: Path) -> bool:
    lowered = path.name.lower()
    return "demo" in lowered or "test" in lowered


def _is_inside_root(path: Path, root: Path) -> bool:
    return path == root or root in path.parents
