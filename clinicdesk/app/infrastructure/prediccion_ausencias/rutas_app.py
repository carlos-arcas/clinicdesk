from __future__ import annotations

from pathlib import Path

from clinicdesk.app.bootstrap import data_dir


def carpeta_datos_app() -> Path:
    """Ruta de datos persistentes para la app (actualmente ./data)."""
    path = data_dir().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path
