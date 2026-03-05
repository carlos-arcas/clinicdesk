from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Generic, TypeVar

from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla


ItemT = TypeVar("ItemT")
SuscriptorEstado = Callable[[EstadoListado[ItemT]], None]


class ListadoViewModelBase(Generic[ItemT]):
    def __init__(self) -> None:
        self._estado: EstadoListado[ItemT] = EstadoListado()
        self._suscriptores: list[SuscriptorEstado[ItemT]] = []

    @property
    def estado(self) -> EstadoListado[ItemT]:
        return self._estado

    def subscribe(self, callback: SuscriptorEstado[ItemT]) -> Callable[[], None]:
        self._suscriptores.append(callback)

        def unsubscribe() -> None:
            if callback in self._suscriptores:
                self._suscriptores.remove(callback)

        return unsubscribe

    def _emit(self) -> None:
        snapshot = replace(self._estado, items=list(self._estado.items))
        for callback in tuple(self._suscriptores):
            callback(snapshot)

    def set_loading(self) -> None:
        self._estado.estado_pantalla = EstadoPantalla.LOADING
        self._estado.error_key = None
        self._emit()

    def set_error(self, error_key: str) -> None:
        self._estado.estado_pantalla = EstadoPantalla.ERROR
        self._estado.error_key = error_key
        self._estado.items = []
        self._emit()

    def set_items(self, items: list[ItemT]) -> None:
        self._estado.items = list(items)
        self._estado.error_key = None
        self._estado.estado_pantalla = EstadoPantalla.EMPTY if not items else EstadoPantalla.CONTENT
        self._emit()

    def normalizar_filtro(self, texto: str, *, to_lower: bool = True) -> str:
        normalizado = texto.strip()
        return normalizado.lower() if to_lower else normalizado
