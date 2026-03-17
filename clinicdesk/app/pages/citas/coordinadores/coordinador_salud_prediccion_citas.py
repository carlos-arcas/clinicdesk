from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from clinicdesk.app.application.prediccion_operativa.ux_estimaciones import debe_mostrar_aviso_salud_estimacion


@dataclass(frozen=True, slots=True)
class EstadoAvisoSaludPrediccionCitas:
    mostrar: bool
    salud_duracion: str
    salud_espera: str


class CoordinadorSaludPrediccionCitas:
    def __init__(self) -> None:
        self._token_refresh_salud = 0
        self._token_aviso_logueado: int | None = None
        self._estimaciones_duracion: dict[int, str] = {}
        self._estimaciones_espera: dict[int, str] = {}

    def registrar_nuevo_refresh(self) -> int:
        self._token_refresh_salud += 1
        self._token_aviso_logueado = None
        return self._token_refresh_salud

    def token_refresh_salud(self) -> int:
        return self._token_refresh_salud

    def actualizar_estimaciones(
        self,
        estimaciones_habilitadas: bool,
        obtener_por_token: Callable[[int], tuple[dict[int, str], dict[int, str]]],
    ) -> tuple[dict[int, str], dict[int, str]]:
        if not estimaciones_habilitadas:
            self._estimaciones_duracion = {}
            self._estimaciones_espera = {}
            return {}, {}
        duraciones, esperas = obtener_por_token(self._token_refresh_salud)
        self._estimaciones_duracion = duraciones
        self._estimaciones_espera = esperas
        return duraciones, esperas

    def estado_aviso_salud(
        self,
        estimaciones_habilitadas: bool,
        salud_duracion: str,
        salud_espera: str,
    ) -> EstadoAvisoSaludPrediccionCitas:
        mostrar = debe_mostrar_aviso_salud_estimacion(
            estimaciones_habilitadas, salud_duracion
        ) or debe_mostrar_aviso_salud_estimacion(estimaciones_habilitadas, salud_espera)
        return EstadoAvisoSaludPrediccionCitas(
            mostrar=mostrar,
            salud_duracion=salud_duracion,
            salud_espera=salud_espera,
        )

    def debe_loguear_aviso(self, mostrar: bool) -> bool:
        return mostrar and self._token_aviso_logueado != self._token_refresh_salud

    def marcar_aviso_logueado(self) -> None:
        self._token_aviso_logueado = self._token_refresh_salud

    def tipos_estimacion_disponibles(self, cita_id: int) -> list[str]:
        disponibles: list[str] = []
        if self._estimaciones_duracion.get(cita_id, "NO_DISPONIBLE") != "NO_DISPONIBLE":
            disponibles.append("duracion")
        if self._estimaciones_espera.get(cita_id, "NO_DISPONIBLE") != "NO_DISPONIBLE":
            disponibles.append("espera")
        return disponibles

    def nivel_estimacion(self, cita_id: int, tipo: str) -> str:
        if tipo == "duracion":
            return self._estimaciones_duracion.get(cita_id, "NO_DISPONIBLE")
        return self._estimaciones_espera.get(cita_id, "NO_DISPONIBLE")
