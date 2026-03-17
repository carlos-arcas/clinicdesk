from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.citas import FiltrosCitasDTO


@dataclass(slots=True)
class EstadoBannerCalidadCitas:
    filtro_activo: str | None = None
    filtros_previos: FiltrosCitasDTO | None = None


class CoordinadorBannersCitas:
    def __init__(self) -> None:
        self._estado = EstadoBannerCalidadCitas()

    def activar_filtro_calidad(self, filtro: str | None, filtros_previos: FiltrosCitasDTO) -> None:
        self._estado = EstadoBannerCalidadCitas(filtro_activo=filtro, filtros_previos=filtros_previos)

    def desactivar_filtro_calidad(self) -> None:
        self._estado = EstadoBannerCalidadCitas()

    def filtro_calidad_activo(self) -> str | None:
        return self._estado.filtro_activo

    def hay_filtro_calidad_activo(self) -> bool:
        return bool(self._estado.filtro_activo)

    def filtros_previos_o(self, por_defecto: FiltrosCitasDTO) -> FiltrosCitasDTO:
        return self._estado.filtros_previos or por_defecto
