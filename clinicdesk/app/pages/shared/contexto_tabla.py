from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget


@dataclass(frozen=True)
class ContextoTablaListado:
    fila_id: int | None
    scroll_vertical: int
    mantener_foco: bool


def capturar_contexto_tabla(tabla: QTableWidget, *, columna_id: int) -> ContextoTablaListado:
    item_actual = tabla.currentItem()
    fila_id: int | None = None
    if item_actual is not None:
        item_id = tabla.item(item_actual.row(), columna_id)
        fila_id = _extraer_id_item(item_id)
    return ContextoTablaListado(
        fila_id=fila_id,
        scroll_vertical=tabla.verticalScrollBar().value(),
        mantener_foco=tabla.hasFocus(),
    )


def restaurar_contexto_tabla(tabla: QTableWidget, contexto: ContextoTablaListado, *, columna_id: int) -> bool:
    restaurado = False
    if contexto.fila_id is not None:
        restaurado = _seleccionar_fila_por_id(tabla, contexto.fila_id, columna_id=columna_id)
    tabla.verticalScrollBar().setValue(contexto.scroll_vertical)
    if contexto.mantener_foco:
        tabla.setFocus()
    return restaurado


def _seleccionar_fila_por_id(tabla: QTableWidget, fila_id: int, *, columna_id: int) -> bool:
    for fila in range(tabla.rowCount()):
        item_id = tabla.item(fila, columna_id)
        if _extraer_id_item(item_id) == fila_id:
            tabla.setCurrentCell(fila, columna_id)
            return True
    return False


def _extraer_id_item(item) -> int | None:
    if item is None:
        return None
    valor = item.data(Qt.UserRole)
    if isinstance(valor, int):
        return valor
    try:
        return int(item.text())
    except (TypeError, ValueError):
        return None
