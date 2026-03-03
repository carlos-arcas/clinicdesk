from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


def debe_mostrar_aviso_salud_prediccion(riesgo_activado: bool, salud_estado: str) -> bool:
    if not riesgo_activado:
        return False
    return salud_estado.upper().strip() in {"AMARILLO", "ROJO"}


@dataclass
class CacheSaludPrediccionPorRefresh(Generic[T]):
    obtener_salud: Callable[[], T]
    _token_cargado: object | None = None
    _salud_cacheada: T | None = None

    def obtener(self, token_refresh: object) -> T:
        if token_refresh != self._token_cargado:
            self._salud_cacheada = self.obtener_salud()
            self._token_cargado = token_refresh
        if self._salud_cacheada is None:
            self._salud_cacheada = self.obtener_salud()
        return self._salud_cacheada
