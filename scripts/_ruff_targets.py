"""Utilidades para resolver targets Python para Ruff."""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Sequence
from pathlib import Path

LOGGER = logging.getLogger(__name__)
LIMITE_COMANDO_RUFF_CHARS = 30000


def resolver_repo_root(desde: Path | None = None) -> Path:
    """Resuelve la raíz del repositorio para comandos dentro de scripts/."""

    base = desde or Path(__file__).resolve()
    return base.parent.parent


def obtener_targets_python(repo_root: Path) -> list[str]:
    """Devuelve archivos *.py versionados; usa '.' como fallback estable."""

    comando = ["git", "-C", str(repo_root), "ls-files"]
    resultado = subprocess.run(comando, check=False, capture_output=True, text=True)
    if resultado.returncode != 0:
        LOGGER.warning("No se pudo resolver archivos versionados con git; se usa '.' como fallback.")
        return ["."]

    targets = [ruta for bruto in resultado.stdout.splitlines() if (ruta := bruto.strip()).endswith(".py")]
    return targets or ["."]


def agrupar_targets_para_comando(
    comando_base: Sequence[str],
    targets: Sequence[str],
    limite_chars: int | None = None,
    max_targets_por_lote: int | None = None,
) -> list[list[str]]:
    """Agrupa targets para no exceder una linea de comando estable."""

    limite = LIMITE_COMANDO_RUFF_CHARS if limite_chars is None else limite_chars
    if not targets:
        return [[]]

    lotes: list[list[str]] = []
    lote_actual: list[str] = []
    for target in targets:
        comando_candidato = [*comando_base, *lote_actual, target]
        excede_limite_chars = lote_actual and len(subprocess.list2cmdline(comando_candidato)) > limite
        excede_limite_targets = max_targets_por_lote is not None and len(lote_actual) >= max_targets_por_lote
        if lote_actual and (excede_limite_chars or excede_limite_targets):
            lotes.append(lote_actual)
            lote_actual = [target]
            continue
        lote_actual.append(target)
    if lote_actual:
        lotes.append(lote_actual)
    return lotes
