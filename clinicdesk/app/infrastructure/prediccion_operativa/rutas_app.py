from __future__ import annotations

from pathlib import Path


_DEFECTO = Path.home() / ".clinicdesk"


def carpeta_datos_app() -> Path:
    root = _DEFECTO
    root.mkdir(parents=True, exist_ok=True)
    return root
