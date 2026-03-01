from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.usecases.obtener_historial_paciente import HistorialPacienteResultado
from clinicdesk.app.i18n import I18nManager


class HistorialPacienteDialog(QDialog):
    def __init__(self, i18n: I18nManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._build_ui()

    def _build_ui(self) -> None:
        self.setMinimumSize(980, 520)
        root = QVBoxLayout(self)

        self.lbl_header = QLabel("")
        root.addWidget(self.lbl_header)

        self.tabs = QTabWidget(self)
        self.tab_resumen = QLabel("")
        self.tab_resumen.setWordWrap(True)
        self.tabs.addTab(self.tab_resumen, self._i18n.t("pacientes.historial.tab.resumen"))

        self.table_citas = QTableWidget(0, 7, self)
        self.table_citas.setHorizontalHeaderLabels(
            [
                self._i18n.t("pacientes.historial.citas.fecha"),
                self._i18n.t("pacientes.historial.citas.hora_inicio"),
                self._i18n.t("pacientes.historial.citas.hora_fin"),
                self._i18n.t("pacientes.historial.citas.medico"),
                self._i18n.t("pacientes.historial.citas.estado"),
                self._i18n.t("pacientes.historial.citas.resumen"),
                self._i18n.t("pacientes.historial.citas.incidencias"),
            ]
        )
        self.tabs.addTab(self.table_citas, self._i18n.t("pacientes.historial.tab.citas"))

        self.table_recetas = QTableWidget(0, 4, self)
        self.table_recetas.setHorizontalHeaderLabels(
            [
                self._i18n.t("pacientes.historial.recetas.id"),
                self._i18n.t("pacientes.historial.recetas.fecha"),
                self._i18n.t("pacientes.historial.recetas.medico"),
                self._i18n.t("pacientes.historial.recetas.estado"),
            ]
        )
        self.tabs.addTab(self.table_recetas, self._i18n.t("pacientes.historial.tab.recetas"))

        self.tab_incidencias = QLabel(self._i18n.t("pacientes.historial.pendiente"))
        self.tabs.addTab(self.tab_incidencias, self._i18n.t("pacientes.historial.tab.incidencias"))
        root.addWidget(self.tabs)

        footer = QHBoxLayout()
        footer.addStretch(1)
        root.addLayout(footer)

    def render_cargando(self) -> None:
        self.lbl_header.setText(self._i18n.t("pacientes.historial.cargando"))

    def render_error(self) -> None:
        self.lbl_header.setText(self._i18n.t("pacientes.historial.error"))
        self.table_citas.setRowCount(0)

    def render_historial(self, data: HistorialPacienteResultado) -> None:
        paciente = data.paciente_detalle
        nombre = f"{paciente.nombre} {paciente.apellidos}".strip()
        self.lbl_header.setText(
            self._i18n.t("pacientes.historial.header").format(
                nombre=nombre,
                documento=paciente.documento,
                telefono=paciente.telefono or "",
                email=paciente.email or "",
            )
        )
        self.tab_resumen.setText(self._i18n.t("pacientes.historial.resumen.descripcion"))
        self._render_citas(data)
        self._render_recetas(data)

    def _render_citas(self, data: HistorialPacienteResultado) -> None:
        self.table_citas.setRowCount(0)
        if not data.citas:
            self.table_citas.setRowCount(1)
            self.table_citas.setItem(0, 0, _item(self._i18n.t("pacientes.historial.sin_citas")))
            return
        for cita in data.citas:
            row = self.table_citas.rowCount()
            self.table_citas.insertRow(row)
            self.table_citas.setItem(row, 0, _item(cita.fecha))
            self.table_citas.setItem(row, 1, _item(cita.hora_inicio))
            self.table_citas.setItem(row, 2, _item(cita.hora_fin))
            self.table_citas.setItem(row, 3, _item(cita.medico))
            self.table_citas.setItem(row, 4, _item(cita.estado))
            resumen = cita.resumen or f"{self._i18n.t('pacientes.historial.citas.longitud')}=0"
            self.table_citas.setItem(row, 5, _item(resumen))
            incidencia = self._i18n.t("comun.si") if cita.tiene_incidencias else self._i18n.t("comun.no")
            self.table_citas.setItem(row, 6, _item(incidencia))

    def _render_recetas(self, data: HistorialPacienteResultado) -> None:
        self.table_recetas.setRowCount(0)
        if not data.recetas:
            self.table_recetas.setRowCount(1)
            self.table_recetas.setItem(0, 0, _item(self._i18n.t("pacientes.historial.recetas.sin_datos")))
            return
        for receta in data.recetas:
            row = self.table_recetas.rowCount()
            self.table_recetas.insertRow(row)
            self.table_recetas.setItem(row, 0, _item(str(receta.id)))
            self.table_recetas.setItem(row, 1, _item(receta.fecha))
            self.table_recetas.setItem(row, 2, _item(receta.medico))
            self.table_recetas.setItem(row, 3, _item(receta.estado))


def _item(texto: str):
    from PySide6.QtWidgets import QTableWidgetItem

    return QTableWidgetItem(texto)
