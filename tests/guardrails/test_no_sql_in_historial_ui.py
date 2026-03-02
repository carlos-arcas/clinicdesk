from __future__ import annotations

from pathlib import Path

RUTAS_UI_HISTORIAL = (
    Path("clinicdesk/app/pages/pacientes/dialogs/historial_paciente_dialog.py"),
    Path("clinicdesk/app/pages/pacientes/dialogs/widgets"),
)
PATRONES_PROHIBIDOS = ("SELECT", ".execute(", "cursor(", "sqlite3")
WHITELIST_LINEAS = (
    "select",  # i18n/labels no SQL
    "self._historial_legacy_uc.execute(self._paciente_id)",
    "self._auditoria_uc.execute(contexto_usuario=self._contexto_usuario, accion=AccionAuditoriaAcceso.VER_DETALLE_RECETA, entidad_tipo=EntidadAuditoriaAcceso.RECETA, entidad_id=receta_id)",
)


def _iter_archivos_objetivo() -> list[Path]:
    archivos: list[Path] = []
    for ruta in RUTAS_UI_HISTORIAL:
        if ruta.is_file():
            archivos.append(ruta)
            continue
        archivos.extend(sorted(ruta.glob("*.py")))
    return archivos


def _linea_permitida(patron: str, linea: str) -> bool:
    linea_normalizada = linea.strip()
    if linea_normalizada.lower() == "select":
        return True
    if patron == ".execute(" and linea_normalizada in WHITELIST_LINEAS:
        return True
    return False


def test_historial_ui_no_contiene_sql_embebido() -> None:
    hallazgos: list[str] = []
    for archivo in _iter_archivos_objetivo():
        for indice, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), start=1):
            for patron in PATRONES_PROHIBIDOS:
                if patron not in linea:
                    continue
                if _linea_permitida(patron, linea):
                    continue
                hallazgos.append(f"{archivo}:{indice} -> {patron}")
    assert not hallazgos, "Se detectó SQL en UI de historial:\n" + "\n".join(hallazgos)
