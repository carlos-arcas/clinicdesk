from __future__ import annotations

from pathlib import Path

RUTAS_UI_CITAS = (
    Path("clinicdesk/app/pages/citas/page.py"),
    *sorted(Path("clinicdesk/app/pages/citas/widgets").glob("*.py")),
)
PATRONES_PROHIBIDOS = ("SELECT", ".execute(", "cursor(", "sqlite3")


def test_no_sql_en_ui_de_citas() -> None:
    offenders: list[str] = []
    for ruta in RUTAS_UI_CITAS:
        contenido = ruta.read_text(encoding="utf-8")
        for patron in PATRONES_PROHIBIDOS:
            if patron in contenido:
                offenders.append(f"{ruta}: {patron}")
    assert not offenders, "SQL detectado en UI de citas:\n" + "\n".join(offenders)
