from __future__ import annotations

from pathlib import Path

RUTA_UI_AUDITORIA = Path("clinicdesk/app/pages/auditoria")
PATRONES_PROHIBIDOS = ("SELECT", ".execute(", "cursor(", "sqlite3")
WHITELIST_LINEAS_CON_EXECUTE = (
    "self._uc_buscar.execute(",
    "self._uc_resumen.execute(",
    "self._uc_exportar.execute(",
)


def test_no_sql_en_ui_de_auditoria() -> None:
    offenders: list[str] = []
    rutas = sorted(RUTA_UI_AUDITORIA.rglob("*.py"))
    for ruta in rutas:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
        for numero, linea in enumerate(lineas, start=1):
            for patron in PATRONES_PROHIBIDOS:
                if patron not in linea:
                    continue
                if patron == ".execute(" and linea_permitida_execute(linea):
                    continue
                offenders.append(f"{ruta}:{numero}: {patron}")
    assert not offenders, "SQL detectado en UI de auditoría:\n" + "\n".join(offenders)


def linea_permitida_execute(linea: str) -> bool:
    return any(token in linea for token in WHITELIST_LINEAS_CON_EXECUTE)
