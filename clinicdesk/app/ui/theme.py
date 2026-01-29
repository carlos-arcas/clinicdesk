from __future__ import annotations

from pathlib import Path


def load_qss() -> str:
    """Carga el QSS principal desde app/ui/styles/main.qss.

    Devuelve cadena vacía si el archivo no existe o falla la lectura.
    """
    qss_path = Path(__file__).parent / "styles" / "main.qss"
    try:
        if not qss_path.exists():
            return ""
        return qss_path.read_text(encoding="utf-8")
    except Exception:
        return ""
