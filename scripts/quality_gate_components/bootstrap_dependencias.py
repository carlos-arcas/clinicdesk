from __future__ import annotations

from pathlib import Path

from .wheelhouse import diagnosticar_wheelhouse


LOCK_DEV = "requirements-dev.txt"


def diagnosticar_wheelhouse_desde_lock(repo_root: Path, wheelhouse: Path, requirements_path: Path | None = None):
    requirements_lock = requirements_path or (repo_root / LOCK_DEV)
    return diagnosticar_wheelhouse(repo_root, wheelhouse, requirements_lock)


def wheelhouse_disponible(repo_root: Path, wheelhouse: Path, requirements_path: Path | None = None) -> bool:
    return diagnosticar_wheelhouse_desde_lock(repo_root, wheelhouse, requirements_path).utilizable


def comando_instalacion(
    python_path: str,
    requirements_path: Path,
    wheelhouse: Path,
    repo_root: Path,
) -> tuple[list[str], str]:
    comando = [python_path, "-m", "pip", "install"]
    if wheelhouse_disponible(repo_root, wheelhouse, requirements_path):
        return [*comando, "--no-index", "--find-links", str(wheelhouse), "-r", str(requirements_path)], "offline"
    return [*comando, "-r", str(requirements_path)], "online"
