from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

from clinicdesk.app.pages.citas.atributos_cita import claves_visibles_por_defecto
from clinicdesk.app.pages.citas.filtros_citas_estado import FiltrosCitasEstado


@dataclass(frozen=True, slots=True)
class PreferenciasCitas:
    filtros: FiltrosCitasEstado
    columnas: list[str]


class PreferenciasCitasStore:
    _ORG = "clinicdesk"
    _APP = "ui"

    def __init__(self, username: str) -> None:
        prefijo = f"citas/{username}"
        self._k_filtros = f"{prefijo}/filtros"
        self._k_columnas = f"{prefijo}/columnas"

    def cargar(self) -> PreferenciasCitas:
        settings = QSettings(self._ORG, self._APP)
        raw_filtros = settings.value(self._k_filtros, {}) or {}
        filtros = FiltrosCitasEstado(
            desde=str(raw_filtros.get("desde", "")),
            hasta=str(raw_filtros.get("hasta", "")),
            texto=str(raw_filtros.get("texto", "")),
            estado=str(raw_filtros.get("estado", "TODOS")),
        )
        raw_columnas = settings.value(self._k_columnas, []) or []
        columnas = [str(col) for col in raw_columnas] if raw_columnas else claves_visibles_por_defecto()
        return PreferenciasCitas(filtros=filtros, columnas=columnas)

    def guardar_filtros(self, filtros: FiltrosCitasEstado) -> None:
        settings = QSettings(self._ORG, self._APP)
        settings.setValue(
            self._k_filtros,
            {
                "desde": filtros.desde,
                "hasta": filtros.hasta,
                "texto": filtros.texto,
                "estado": filtros.estado,
            },
        )

    def guardar_columnas(self, columnas: list[str]) -> None:
        settings = QSettings(self._ORG, self._APP)
        settings.setValue(self._k_columnas, columnas)
