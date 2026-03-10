from __future__ import annotations

from pathlib import Path
import os


def resolver_wheelhouse(repo_root: Path) -> Path:
    ruta = os.environ.get("CLINICDESK_WHEELHOUSE")
    if ruta:
        return Path(ruta).expanduser().resolve()
    return repo_root / "wheelhouse"


def wheelhouse_disponible(wheelhouse: Path) -> bool:
    if not wheelhouse.exists() or not wheelhouse.is_dir():
        return False
    return any(wheelhouse.glob("*.whl"))


def comando_instalacion(
    python_path: str,
    requirements_path: Path,
    wheelhouse: Path,
) -> tuple[list[str], str]:
    comando = [python_path, "-m", "pip", "install"]
    if wheelhouse_disponible(wheelhouse):
        return [*comando, "--no-index", "--find-links", str(wheelhouse), "-r", str(requirements_path)], "offline"
    return [*comando, "-r", str(requirements_path)], "online"
