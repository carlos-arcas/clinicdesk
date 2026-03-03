from __future__ import annotations

import re
from pathlib import Path

RUTA_APP = Path("clinicdesk/app")
PATRON_IMPORT_QSETTINGS_QTWIDGETS = re.compile(r"from\s+PySide6\.QtWidgets\s+import\s+.*\bQSettings\b")
USO_QTWIDGETS_QSETTINGS = "QtWidgets.QSettings"


def _iter_archivos_app() -> list[Path]:
    return sorted(RUTA_APP.glob("**/*.py"))


def test_no_se_importa_qsettings_desde_qtwidgets() -> None:
    hallazgos: list[str] = []
    for archivo in _iter_archivos_app():
        for indice, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), start=1):
            if PATRON_IMPORT_QSETTINGS_QTWIDGETS.search(linea):
                hallazgos.append(f"{archivo}:{indice} -> import QSettings desde QtWidgets")
            if USO_QTWIDGETS_QSETTINGS in linea:
                hallazgos.append(f"{archivo}:{indice} -> uso de QtWidgets.QSettings")
    assert not hallazgos, "Se detectaron usos inválidos de QSettings:\n" + "\n".join(hallazgos)
