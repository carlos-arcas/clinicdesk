from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

from clinicdesk.app.ui.ux.contexto_tabla import ContextoTablaListado, FilaTabla, construir_contexto_tabla, resolver_fila_a_restaurar

if TYPE_CHECKING:
    from PySide6.QtWidgets import QTableWidget


def capturar_contexto_tabla(tabla: QTableWidget, *, columna_id: int) -> ContextoTablaListado:
    item_actual = tabla.currentItem()
    fila_id: int | None = None
    if item_actual is not None:
        item_id = tabla.item(item_actual.row(), columna_id)
        fila_id = _extraer_id_item(item_id)
    return construir_contexto_tabla(
        fila_id=fila_id,
        scroll_vertical=tabla.verticalScrollBar().value(),
        mantener_foco=tabla.hasFocus(),
    )


def restaurar_contexto_tabla(tabla: QTableWidget, contexto: ContextoTablaListado, *, columna_id: int) -> bool:
    filas = _extraer_filas(tabla, columna_id=columna_id)
    fila_objetivo = resolver_fila_a_restaurar(filas, fila_id_objetivo=contexto.fila_id)
    restaurado = fila_objetivo is not None
    if restaurado:
        tabla.setCurrentCell(fila_objetivo, columna_id)
    tabla.verticalScrollBar().setValue(contexto.scroll_vertical)
    if contexto.mantener_foco:
        tabla.setFocus()
    return restaurado


def _extraer_filas(tabla: QTableWidget, *, columna_id: int) -> list[FilaTabla]:
    filas: list[FilaTabla] = []
    for indice in range(tabla.rowCount()):
        item_id = tabla.item(indice, columna_id)
        filas.append(FilaTabla(fila=indice, fila_id=_extraer_id_item(item_id)))
    return filas


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
