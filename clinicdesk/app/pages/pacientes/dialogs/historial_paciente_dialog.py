from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.usecases.obtener_detalle_cita import ObtenerDetalleCita
from clinicdesk.app.application.usecases.obtener_historial_paciente import HistorialPacienteResultado, RecetaResumen
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pacientes.dialogs.detalle_cita_dialog import DetalleCitaDialog
from clinicdesk.app.pages.pacientes.dialogs.detalle_receta_dialog import DetalleRecetaDialog


class HistorialPacienteDialog(QDialog):
    def __init__(self, i18n: I18nManager, detalle_cita_uc: ObtenerDetalleCita, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._detalle_cita_uc = detalle_cita_uc
        self._historial: HistorialPacienteResultado | None = None
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
        self.tabs.addTab(self._build_tab_citas(), self._i18n.t("pacientes.historial.tab.citas"))
        self.tabs.addTab(self._build_tab_recetas(), self._i18n.t("pacientes.historial.tab.recetas"))
        self.tabs.addTab(QLabel(self._i18n.t("pacientes.historial.pendiente")), self._i18n.t("pacientes.historial.tab.incidencias"))
        root.addWidget(self.tabs)

    def _build_tab_citas(self) -> QWidget:
        tab = QWidget(self)
        root = QVBoxLayout(tab)
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
        self.table_citas.itemSelectionChanged.connect(self._actualizar_acciones_citas)
        self.table_citas.itemDoubleClicked.connect(lambda _: self._abrir_detalle_cita())
        root.addWidget(self.table_citas)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.btn_ver_informe = QPushButton(self._i18n.t("pacientes.historial.citas.ver_informe"), self)
        self.btn_ver_informe.clicked.connect(self._abrir_detalle_cita)
        self.btn_ver_informe.setEnabled(False)
        actions.addWidget(self.btn_ver_informe)
        root.addLayout(actions)
        return tab

    def _build_tab_recetas(self) -> QWidget:
        tab = QWidget(self)
        root = QVBoxLayout(tab)
        actions = QHBoxLayout()
        self.combo_filtro_recetas = QComboBox(self)
        self.combo_filtro_recetas.addItem(self._i18n.t("pacientes.historial.recetas.filtro.todas"), "todas")
        self.combo_filtro_recetas.addItem(self._i18n.t("pacientes.historial.recetas.filtro.activas"), "activas")
        self.combo_filtro_recetas.currentIndexChanged.connect(self._aplicar_filtro_recetas)
        self.btn_ver_detalle = QPushButton(self._i18n.t("pacientes.historial.recetas.ver_detalle"), self)
        self.btn_ver_detalle.clicked.connect(self._abrir_detalle_receta)
        actions.addWidget(QLabel(self._i18n.t("pacientes.historial.recetas.filtro.label")))
        actions.addWidget(self.combo_filtro_recetas)
        actions.addStretch(1)
        actions.addWidget(self.btn_ver_detalle)
        root.addLayout(actions)

        self.table_recetas = QTableWidget(0, 5, self)
        self.table_recetas.setHorizontalHeaderLabels(
            [
                self._i18n.t("pacientes.historial.recetas.fecha"),
                self._i18n.t("pacientes.historial.recetas.medico"),
                self._i18n.t("pacientes.historial.recetas.estado"),
                self._i18n.t("pacientes.historial.recetas.num_lineas"),
                self._i18n.t("pacientes.historial.recetas.activa"),
            ]
        )
        self.table_recetas.itemSelectionChanged.connect(self._actualizar_lineas_receta)
        self.table_recetas.itemDoubleClicked.connect(lambda _: self._abrir_detalle_receta())
        root.addWidget(self.table_recetas)

        self.table_lineas = QTableWidget(0, 5, self)
        self.table_lineas.setHorizontalHeaderLabels(
            [
                self._i18n.t("pacientes.historial.recetas.lineas.medicamento"),
                self._i18n.t("pacientes.historial.recetas.lineas.posologia"),
                self._i18n.t("pacientes.historial.recetas.lineas.inicio"),
                self._i18n.t("pacientes.historial.recetas.lineas.fin"),
                self._i18n.t("pacientes.historial.recetas.lineas.estado"),
            ]
        )
        root.addWidget(self.table_lineas)

        self.lbl_recetas_estado = QLabel("")
        self.lbl_recetas_estado.setAlignment(Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self.lbl_recetas_estado)
        return tab

    def render_cargando(self) -> None:
        self.lbl_header.setText(self._i18n.t("pacientes.historial.cargando"))
        self.lbl_recetas_estado.setText(self._i18n.t("pacientes.historial.cargando"))

    def render_error(self) -> None:
        self.lbl_header.setText(self._i18n.t("pacientes.historial.error"))
        self.table_citas.setRowCount(0)
        self.table_recetas.setRowCount(0)
        self.table_lineas.setRowCount(0)
        self.lbl_recetas_estado.setText(self._i18n.t("pacientes.historial.recetas.error"))

    def render_historial(self, data: HistorialPacienteResultado) -> None:
        self._historial = data
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
        self._configurar_filtro_activo(data)
        self._aplicar_filtro_recetas()

    def _configurar_filtro_activo(self, data: HistorialPacienteResultado) -> None:
        self.combo_filtro_recetas.setEnabled(data.filtro_activas_habilitado)
        self.combo_filtro_recetas.setToolTip(data.filtro_activas_tooltip or "")

    def _render_citas(self, data: HistorialPacienteResultado) -> None:
        self.table_citas.setRowCount(0)
        if not data.citas:
            self.table_citas.setRowCount(1)
            self.table_citas.setItem(0, 0, QTableWidgetItem(self._i18n.t("pacientes.historial.sin_citas")))
            self._actualizar_acciones_citas()
            return
        for cita in data.citas:
            row = self.table_citas.rowCount()
            self.table_citas.insertRow(row)
            self.table_citas.setItem(row, 0, QTableWidgetItem(cita.fecha))
            self.table_citas.setItem(row, 1, QTableWidgetItem(cita.hora_inicio))
            self.table_citas.setItem(row, 2, QTableWidgetItem(cita.hora_fin))
            self.table_citas.setItem(row, 3, QTableWidgetItem(cita.medico))
            self.table_citas.setItem(row, 4, QTableWidgetItem(cita.estado))
            resumen = cita.resumen or f"{self._i18n.t('pacientes.historial.citas.longitud')}=0"
            self.table_citas.setItem(row, 5, QTableWidgetItem(resumen))
            incidencia = self._i18n.t("comun.si") if cita.tiene_incidencias else self._i18n.t("comun.no")
            self.table_citas.setItem(row, 6, QTableWidgetItem(incidencia))
            self.table_citas.item(row, 0).setData(Qt.ItemDataRole.UserRole, cita.id)
        self.table_citas.setCurrentCell(0, 0)
        self._actualizar_acciones_citas()

    def _actualizar_acciones_citas(self) -> None:
        self.btn_ver_informe.setEnabled(self._cita_id_seleccionada() is not None)

    def _abrir_detalle_cita(self) -> None:
        cita_id = self._cita_id_seleccionada()
        if cita_id is None:
            return
        dialog = DetalleCitaDialog(self._i18n, usecase=self._detalle_cita_uc, cita_id=cita_id, parent=self)
        dialog.exec()

    def _cita_id_seleccionada(self) -> int | None:
        current = self.table_citas.currentItem()
        if current is None:
            return None
        item = self.table_citas.item(current.row(), 0)
        if item is None:
            return None
        cita_id = item.data(Qt.ItemDataRole.UserRole)
        return int(cita_id) if cita_id is not None else None

    def _aplicar_filtro_recetas(self) -> None:
        if self._historial is None:
            return
        filtro = self.combo_filtro_recetas.currentData()
        recetas = self._historial.recetas
        if filtro == "activas":
            recetas = tuple(receta for receta in recetas if receta.activa)
        self._render_recetas(recetas)

    def _render_recetas(self, recetas: tuple[RecetaResumen, ...]) -> None:
        self.table_recetas.setRowCount(0)
        self.table_lineas.setRowCount(0)
        if not recetas:
            self.lbl_recetas_estado.setText(self._i18n.t("pacientes.historial.recetas.sin_registros"))
            return
        self.lbl_recetas_estado.setText("")
        for receta in recetas:
            row = self.table_recetas.rowCount()
            self.table_recetas.insertRow(row)
            self.table_recetas.setItem(row, 0, QTableWidgetItem(receta.fecha))
            self.table_recetas.setItem(row, 1, QTableWidgetItem(receta.medico))
            self.table_recetas.setItem(row, 2, QTableWidgetItem(receta.estado))
            self.table_recetas.setItem(row, 3, QTableWidgetItem(str(receta.num_lineas)))
            activa = self._i18n.t("comun.si") if receta.activa else self._i18n.t("comun.no")
            self.table_recetas.setItem(row, 4, QTableWidgetItem(activa))
            self.table_recetas.item(row, 0).setData(Qt.ItemDataRole.UserRole, receta.id)
        self.table_recetas.setCurrentCell(0, 0)

    def _actualizar_lineas_receta(self) -> None:
        self.table_lineas.setRowCount(0)
        if self._historial is None:
            return
        receta_id = self._receta_id_seleccionada()
        if receta_id is None:
            return
        lineas = self._historial.detalle_por_receta.get(receta_id, ())
        for linea in lineas:
            row = self.table_lineas.rowCount()
            self.table_lineas.insertRow(row)
            self.table_lineas.setItem(row, 0, QTableWidgetItem(linea.medicamento))
            self.table_lineas.setItem(row, 1, QTableWidgetItem(linea.posologia))
            self.table_lineas.setItem(row, 2, QTableWidgetItem(linea.inicio))
            self.table_lineas.setItem(row, 3, QTableWidgetItem(linea.fin))
            self.table_lineas.setItem(row, 4, QTableWidgetItem(linea.estado))

    def _abrir_detalle_receta(self) -> None:
        if self._historial is None:
            return
        receta_id = self._receta_id_seleccionada()
        if receta_id is None:
            return
        receta = next((item for item in self._historial.recetas if item.id == receta_id), None)
        if receta is None:
            return
        lineas = self._historial.detalle_por_receta.get(receta_id, ())
        dialog = DetalleRecetaDialog(self._i18n, receta=receta, lineas=lineas, parent=self)
        dialog.exec()

    def _receta_id_seleccionada(self) -> int | None:
        current = self.table_recetas.currentItem()
        if current is None:
            return None
        receta_id = self.table_recetas.item(current.row(), 0).data(Qt.ItemDataRole.UserRole)
        return int(receta_id) if receta_id is not None else None
