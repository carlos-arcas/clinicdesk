from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from clinicdesk.app.pages.shared.contexto_tabla import capturar_contexto_tabla, restaurar_contexto_tabla


def _crear_tabla() -> QTableWidget:
    tabla = QTableWidget(0, 2)
    for idx in range(6):
        tabla.insertRow(idx)
        item_id = QTableWidgetItem(f"fila-{idx}")
        item_id.setData(Qt.UserRole, idx + 100)
        tabla.setItem(idx, 0, item_id)
        tabla.setItem(idx, 1, QTableWidgetItem(f"Nombre {idx}"))
    return tabla


def test_contexto_tabla_restaurar_seleccion_y_scroll(qtbot) -> None:
    tabla = _crear_tabla()
    qtbot.addWidget(tabla)
    tabla.show()
    tabla.setCurrentCell(4, 0)
    tabla.verticalScrollBar().setValue(7)

    contexto = capturar_contexto_tabla(tabla, columna_id=0)

    tabla.setCurrentCell(0, 0)
    tabla.verticalScrollBar().setValue(0)

    restaurado = restaurar_contexto_tabla(tabla, contexto, columna_id=0)

    assert restaurado is True
    assert tabla.currentItem() is not None
    assert tabla.currentItem().data(Qt.UserRole) == 104
    assert tabla.verticalScrollBar().value() == 7


def test_contexto_tabla_sin_id_retorna_false(qtbot) -> None:
    tabla = _crear_tabla()
    qtbot.addWidget(tabla)
    tabla.show()
    contexto = capturar_contexto_tabla(tabla, columna_id=0)

    tabla.clearContents()
    restaurado = restaurar_contexto_tabla(tabla, contexto, columna_id=0)

    assert restaurado is False
