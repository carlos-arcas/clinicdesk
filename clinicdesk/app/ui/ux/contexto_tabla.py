from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextoTablaListado:
    fila_id: int | None
    scroll_vertical: int
    mantener_foco: bool


@dataclass(frozen=True, slots=True)
class FilaTabla:
    fila: int
    fila_id: int | None


def construir_contexto_tabla(*, fila_id: int | None, scroll_vertical: int, mantener_foco: bool) -> ContextoTablaListado:
    return ContextoTablaListado(
        fila_id=fila_id,
        scroll_vertical=scroll_vertical,
        mantener_foco=mantener_foco,
    )


def resolver_fila_a_restaurar(filas: list[FilaTabla], *, fila_id_objetivo: int | None) -> int | None:
    if fila_id_objetivo is None:
        return None
    for fila in filas:
        if fila.fila_id == fila_id_objetivo:
            return fila.fila
    return None
