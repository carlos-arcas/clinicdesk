from __future__ import annotations

from typing import Iterable, Optional

from PySide6.QtWidgets import QDialog, QLabel, QTableWidget, QVBoxLayout, QWidget

from clinicdesk.app.application.usecases.obtener_historial_paciente import LineaRecetaResumen, RecetaResumen
from clinicdesk.app.i18n import I18nManager


class DetalleRecetaDialog(QDialog):
    def __init__(
        self,
        i18n: I18nManager,
        receta: RecetaResumen,
        lineas: Iterable[LineaRecetaResumen],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._build_ui(receta, tuple(lineas))

    def _build_ui(self, receta: RecetaResumen, lineas: tuple[LineaRecetaResumen, ...]) -> None:
        self.setMinimumWidth(760)
        self.setWindowTitle(self._i18n.t("pacientes.historial.recetas.detalle.titulo"))
        root = QVBoxLayout(self)

        header = self._i18n.t("pacientes.historial.recetas.detalle.header").format(
            id=receta.id,
            fecha=receta.fecha,
            medico=receta.medico,
            estado=receta.estado,
        )
        root.addWidget(QLabel(header))

        table = QTableWidget(0, 5, self)
        table.setHorizontalHeaderLabels(
            [
                self._i18n.t("pacientes.historial.recetas.lineas.medicamento"),
                self._i18n.t("pacientes.historial.recetas.lineas.posologia"),
                self._i18n.t("pacientes.historial.recetas.lineas.inicio"),
                self._i18n.t("pacientes.historial.recetas.lineas.fin"),
                self._i18n.t("pacientes.historial.recetas.lineas.estado"),
            ]
        )
        for linea in lineas:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, _item(linea.medicamento))
            table.setItem(row, 1, _item(linea.posologia))
            table.setItem(row, 2, _item(linea.inicio))
            table.setItem(row, 3, _item(linea.fin))
            table.setItem(row, 4, _item(linea.estado))
        root.addWidget(table)


def _item(texto: str):
    from PySide6.QtWidgets import QTableWidgetItem

    return QTableWidgetItem(texto)
