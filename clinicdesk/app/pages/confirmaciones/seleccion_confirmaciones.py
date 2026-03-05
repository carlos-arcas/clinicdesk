from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem


_COL_CHECK = 0


def toggle_todo_visible(tabla, state: int, actualizar_cita_seleccionada, actualizar_estado_seleccion) -> None:
    check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
    tabla.blockSignals(True)
    for row in range(tabla.rowCount()):
        item = tabla.item(row, _COL_CHECK)
        if item is not None:
            item.setCheckState(check_state)
            actualizar_cita_seleccionada(item)
    tabla.blockSignals(False)
    actualizar_estado_seleccion()


def on_item_changed(item: QTableWidgetItem, actualizar_cita_seleccionada, seleccionar_en_vm, actualizar_estado_seleccion) -> None:
    if item.column() != _COL_CHECK:
        return
    actualizar_cita_seleccionada(item)
    cita_id = item.data(Qt.UserRole)
    if isinstance(cita_id, int) and item.checkState() == Qt.Checked:
        seleccionar_en_vm(cita_id)
    actualizar_estado_seleccion()


def actualizar_cita_seleccionada(item: QTableWidgetItem, citas_seleccionadas: set[int]) -> None:
    cita_id = item.data(Qt.UserRole)
    if not isinstance(cita_id, int):
        return
    if item.checkState() == Qt.Checked:
        citas_seleccionadas.add(cita_id)
        return
    citas_seleccionadas.discard(cita_id)
