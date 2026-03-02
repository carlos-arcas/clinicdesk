from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QSettings, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso
from clinicdesk.app.application.historial_paciente import (
    ATRIBUTOS_HISTORIAL_CITAS,
    ATRIBUTOS_HISTORIAL_RECETAS,
    BuscarHistorialCitasPaciente,
    BuscarHistorialRecetasPaciente,
    ObtenerResumenHistorialPaciente,
    normalizar_filtros_historial_paciente,
    sanear_columnas_solicitadas,
)
from clinicdesk.app.application.security import UserContext
from clinicdesk.app.application.usecases.obtener_detalle_cita import ObtenerDetalleCita
from clinicdesk.app.application.usecases.obtener_historial_paciente import HistorialPacienteResultado, ObtenerHistorialPaciente
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import RegistrarAuditoriaAcceso
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pacientes.dialogs.detalle_cita_dialog import DetalleCitaDialog
from clinicdesk.app.pages.pacientes.dialogs.detalle_receta_dialog import DetalleRecetaDialog
from clinicdesk.app.pages.pacientes.dialogs.widgets.dialogo_selector_columnas_historial import DialogoSelectorColumnasHistorial
from clinicdesk.app.pages.pacientes.dialogs.widgets.panel_filtros_historial_paciente_widget import PanelFiltrosHistorialPacienteWidget
from clinicdesk.app.pages.pacientes.dialogs.widgets.persistencia_historial_settings import (
    EstadoPersistidoFiltros,
    deserializar_filtros,
    key_columnas,
    key_filtros,
    sanear_columnas_guardadas,
    serializar_columnas,
    serializar_filtros,
)

_ESTADOS_CITAS = ("PROGRAMADA", "CONFIRMADA", "REALIZADA", "NO_PRESENTADO", "CANCELADA")
_ESTADOS_RECETAS = ("ACTIVA", "PENDIENTE", "DISPENSADA", "FINALIZADA", "ANULADA", "CANCELADA")


class HistorialPacienteDialog(QDialog):
    def __init__(self, i18n: I18nManager, paciente_id: int, buscar_citas_uc: BuscarHistorialCitasPaciente, buscar_recetas_uc: BuscarHistorialRecetasPaciente, resumen_uc: ObtenerResumenHistorialPaciente, historial_legacy_uc: ObtenerHistorialPaciente, detalle_cita_uc: ObtenerDetalleCita, auditoria_uc: RegistrarAuditoriaAcceso, contexto_usuario: UserContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._paciente_id = paciente_id
        self._buscar_citas_uc = buscar_citas_uc
        self._buscar_recetas_uc = buscar_recetas_uc
        self._resumen_uc = resumen_uc
        self._historial_legacy_uc = historial_legacy_uc
        self._detalle_cita_uc = detalle_cita_uc
        self._auditoria_uc = auditoria_uc
        self._contexto_usuario = contexto_usuario
        self._settings = QSettings("ClinicDesk", "ClinicDesk")
        self._historial_base: HistorialPacienteResultado | None = None
        self._columnas_citas = self._cargar_columnas("citas", ATRIBUTOS_HISTORIAL_CITAS)
        self._columnas_recetas = self._cargar_columnas("recetas", ATRIBUTOS_HISTORIAL_RECETAS)
        self._build_ui()
        self._i18n.subscribe(self.retranslate_ui)
        self._cargar_estado_inicial()

    def _build_ui(self) -> None:
        self.setMinimumSize(980, 520)
        root = QVBoxLayout(self)
        self.lbl_header = QLabel("")
        root.addWidget(self.lbl_header)
        self._crear_panel_resumen(root)
        self.panel_filtros = PanelFiltrosHistorialPacienteWidget(self._i18n, self)
        self.panel_filtros.aplicar_solicitado.connect(self._aplicar_filtros)
        self.panel_filtros.limpiar_solicitado.connect(self._limpiar_filtros)
        root.addWidget(self.panel_filtros)
        self.tabs = QTabWidget(self)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.addTab(self._build_tab_citas(), "")
        self.tabs.addTab(self._build_tab_recetas(), "")
        root.addWidget(self.tabs)
        self.lbl_estado = QLabel("")
        root.addWidget(self.lbl_estado)
        self.retranslate_ui()

    def _crear_panel_resumen(self, root: QVBoxLayout) -> None:
        fila = QHBoxLayout()
        self.lbl_resumen_titulo = QLabel("")
        self.lbl_kpis = QLabel("")
        self.btn_actualizar = QPushButton("")
        self.btn_actualizar.clicked.connect(self._aplicar_filtros)
        self.btn_reintentar_resumen = QPushButton("")
        self.btn_reintentar_resumen.clicked.connect(self._actualizar_resumen)
        self.btn_reintentar_resumen.setVisible(False)
        fila.addWidget(self.lbl_resumen_titulo)
        fila.addStretch(1)
        fila.addWidget(self.lbl_kpis)
        fila.addWidget(self.btn_reintentar_resumen)
        fila.addWidget(self.btn_actualizar)
        root.addLayout(fila)

    def _build_tab_citas(self) -> QWidget:
        tab = QWidget(self)
        root = QVBoxLayout(tab)
        actions = QHBoxLayout()
        self.btn_columnas_citas = QPushButton(self)
        self.btn_columnas_citas.clicked.connect(lambda: self._seleccionar_columnas("citas"))
        self.btn_ver_informe = QPushButton(self)
        self.btn_ver_informe.clicked.connect(self._abrir_detalle_cita)
        actions.addWidget(self.btn_columnas_citas)
        actions.addStretch(1)
        actions.addWidget(self.btn_ver_informe)
        root.addLayout(actions)
        self.table_citas = QTableWidget(0, 0, self)
        self.table_citas.itemSelectionChanged.connect(self._actualizar_acciones)
        self.table_citas.itemDoubleClicked.connect(lambda _: self._abrir_detalle_cita())
        root.addWidget(self.table_citas)
        return tab

    def _build_tab_recetas(self) -> QWidget:
        tab = QWidget(self)
        root = QVBoxLayout(tab)
        actions = QHBoxLayout()
        self.btn_columnas_recetas = QPushButton(self)
        self.btn_columnas_recetas.clicked.connect(lambda: self._seleccionar_columnas("recetas"))
        self.btn_ver_detalle = QPushButton(self)
        self.btn_ver_detalle.clicked.connect(self._abrir_detalle_receta)
        actions.addWidget(self.btn_columnas_recetas)
        actions.addStretch(1)
        actions.addWidget(self.btn_ver_detalle)
        root.addLayout(actions)
        self.table_recetas = QTableWidget(0, 0, self)
        self.table_recetas.itemSelectionChanged.connect(self._actualizar_lineas_receta)
        self.table_recetas.itemDoubleClicked.connect(lambda _: self._abrir_detalle_receta())
        root.addWidget(self.table_recetas)
        self.table_lineas = QTableWidget(0, 5, self)
        root.addWidget(self.table_lineas)
        return tab

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self._i18n.t("pacientes.historial.titulo"))
        self.lbl_resumen_titulo.setText(self._i18n.t("historial.resumen.titulo"))
        self.btn_actualizar.setText(self._i18n.t("historial.resumen.actualizar"))
        self.btn_reintentar_resumen.setText(self._i18n.t("historial.estado.reintentar"))
        self.btn_columnas_citas.setText(self._i18n.t("historial.columnas.boton"))
        self.btn_columnas_recetas.setText(self._i18n.t("historial.columnas.boton"))
        self.btn_ver_informe.setText(self._i18n.t("pacientes.historial.citas.ver_informe"))
        self.btn_ver_detalle.setText(self._i18n.t("pacientes.historial.recetas.ver_detalle"))
        self.tabs.setTabText(0, self._i18n.t("pacientes.historial.tab.citas"))
        self.tabs.setTabText(1, self._i18n.t("pacientes.historial.tab.recetas"))
        self.table_lineas.setHorizontalHeaderLabels([self._i18n.t("pacientes.historial.recetas.lineas.medicamento"), self._i18n.t("pacientes.historial.recetas.lineas.posologia"), self._i18n.t("pacientes.historial.recetas.lineas.inicio"), self._i18n.t("pacientes.historial.recetas.lineas.fin"), self._i18n.t("pacientes.historial.recetas.lineas.estado")])
        self.panel_filtros.retranslate_ui()

    def _cargar_estado_inicial(self) -> None:
        self._historial_base = self._historial_legacy_uc.execute(self._paciente_id)
        if self._historial_base is None:
            self.lbl_estado.setText(self._i18n.t("historial.estado.error"))
            return
        paciente = self._historial_base.paciente_detalle
        self.lbl_header.setText(self._i18n.t("pacientes.historial.header").format(nombre=f"{paciente.nombre} {paciente.apellidos}".strip(), documento=paciente.documento, telefono=paciente.telefono or "", email=paciente.email or ""))
        self._restaurar_filtros()
        self._actualizar_catalogo_estados()
        self._aplicar_filtros()

    def _aplicar_filtros(self) -> None:
        self._set_estado_cargando()
        filtros = normalizar_filtros_historial_paciente(self.panel_filtros.construir_filtros(self._paciente_id), ahora=datetime.now())
        self._guardar_filtros(filtros)
        self._actualizar_resumen(filtros)
        if self.tabs.currentIndex() == 0:
            resultado = self._buscar_citas_uc.ejecutar(filtros, self._columnas_citas)
            self._render_tabla(self.table_citas, ATRIBUTOS_HISTORIAL_CITAS, self._columnas_citas, resultado.items, "cita_id")
        else:
            resultado = self._buscar_recetas_uc.ejecutar(filtros, self._columnas_recetas)
            self._render_tabla(self.table_recetas, ATRIBUTOS_HISTORIAL_RECETAS, self._columnas_recetas, resultado.items, "receta_id")
        self.lbl_estado.setText(self._i18n.t("historial.estado.vacio") if resultado.total == 0 else "")
        self._actualizar_acciones()

    def _render_tabla(self, tabla: QTableWidget, contrato, columnas: tuple[str, ...], items, id_key: str) -> None:
        columnas_visibles = [item for item in contrato if item.clave in columnas]
        tabla.setColumnCount(len(columnas_visibles))
        tabla.setHorizontalHeaderLabels([self._i18n.t(item.i18n_key_cabecera) for item in columnas_visibles])
        tabla.setRowCount(0)
        for fila in items:
            row = tabla.rowCount()
            tabla.insertRow(row)
            for col, descriptor in enumerate(columnas_visibles):
                tabla.setItem(row, col, QTableWidgetItem(descriptor.formateador(fila)))
            tabla.item(row, 0).setData(Qt.ItemDataRole.UserRole, fila.get(id_key))

    def _actualizar_resumen(self, filtros=None) -> None:
        self.lbl_kpis.setText(self._i18n.t("historial.estado.cargando"))
        self.btn_reintentar_resumen.setVisible(False)
        try:
            ventana = None if filtros is None or filtros.rango_preset != "30_DIAS" else 30
            data = self._resumen_uc.ejecutar(self._paciente_id, ventana_dias=ventana)
            self.lbl_kpis.setText(self._i18n.t("historial.resumen.kpi").format(citas=data.total_citas, ausencias=data.no_presentados, recetas=data.total_recetas, activas=data.recetas_activas))
        except Exception:
            self.lbl_kpis.setText(self._i18n.t("historial.resumen.error"))
            self.btn_reintentar_resumen.setVisible(True)

    def _actualizar_lineas_receta(self) -> None:
        self.table_lineas.setRowCount(0)
        receta_id = self._id_seleccionado(self.table_recetas)
        if self._historial_base is None or receta_id is None:
            self.lbl_estado.setText(self._i18n.t("historial.recetas.selecciona"))
            return
        self.lbl_estado.setText("")
        for linea in self._historial_base.detalle_por_receta.get(receta_id, ()):
            row = self.table_lineas.rowCount()
            self.table_lineas.insertRow(row)
            self.table_lineas.setItem(row, 0, QTableWidgetItem(linea.medicamento))
            self.table_lineas.setItem(row, 1, QTableWidgetItem(linea.posologia))
            self.table_lineas.setItem(row, 2, QTableWidgetItem(linea.inicio))
            self.table_lineas.setItem(row, 3, QTableWidgetItem(linea.fin))
            self.table_lineas.setItem(row, 4, QTableWidgetItem(linea.estado))

    def _on_tab_changed(self) -> None:
        self._actualizar_catalogo_estados()
        self._aplicar_filtros()

    def _actualizar_catalogo_estados(self) -> None:
        self.panel_filtros.set_estados(_ESTADOS_CITAS if self.tabs.currentIndex() == 0 else _ESTADOS_RECETAS)

    def _seleccionar_columnas(self, pestaña: str) -> None:
        contrato = ATRIBUTOS_HISTORIAL_CITAS if pestaña == "citas" else ATRIBUTOS_HISTORIAL_RECETAS
        actuales = self._columnas_citas if pestaña == "citas" else self._columnas_recetas
        dialog = DialogoSelectorColumnasHistorial(self._i18n, contrato, actuales, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        columnas = sanear_columnas_solicitadas(dialog.columnas_seleccionadas(), contrato)
        if pestaña == "citas":
            self._columnas_citas = columnas
        else:
            self._columnas_recetas = columnas
        self._settings.setValue(key_columnas(pestaña), serializar_columnas(columnas))
        self._aplicar_filtros()

    def _cargar_columnas(self, pestaña: str, contrato):
        valor = str(self._settings.value(key_columnas(pestaña), ""))
        return sanear_columnas_solicitadas(sanear_columnas_guardadas(valor), contrato)

    def _restaurar_filtros(self) -> None:
        data = EstadoPersistidoFiltros(
            preset=str(self._settings.value(f"{key_filtros()}/preset", "30_DIAS")),
            desde_iso=self._settings.value(f"{key_filtros()}/desde", None),
            hasta_iso=self._settings.value(f"{key_filtros()}/hasta", None),
            texto=self._settings.value(f"{key_filtros()}/texto", None),
            estado=self._settings.value(f"{key_filtros()}/estado", None),
        )
        self.panel_filtros.cargar_desde_dto(deserializar_filtros(self._paciente_id, data))

    def _guardar_filtros(self, filtros) -> None:
        data = serializar_filtros(filtros)
        self._settings.setValue(f"{key_filtros()}/preset", data.preset)
        self._settings.setValue(f"{key_filtros()}/desde", data.desde_iso)
        self._settings.setValue(f"{key_filtros()}/hasta", data.hasta_iso)
        self._settings.setValue(f"{key_filtros()}/texto", data.texto)
        self._settings.setValue(f"{key_filtros()}/estado", data.estado)

    def _limpiar_filtros(self) -> None:
        self.panel_filtros.limpiar()
        self._aplicar_filtros()

    def _abrir_detalle_cita(self) -> None:
        cita_id = self._id_seleccionado(self.table_citas)
        if cita_id is None:
            return
        DetalleCitaDialog(self._i18n, usecase=self._detalle_cita_uc, auditoria_uc=self._auditoria_uc, contexto_usuario=self._contexto_usuario, cita_id=cita_id, parent=self).exec()

    def _abrir_detalle_receta(self) -> None:
        receta_id = self._id_seleccionado(self.table_recetas)
        if receta_id is None or self._historial_base is None:
            return
        receta = next((item for item in self._historial_base.recetas if item.id == receta_id), None)
        if receta is None:
            return
        self._auditoria_uc.execute(contexto_usuario=self._contexto_usuario, accion=AccionAuditoriaAcceso.VER_DETALLE_RECETA, entidad_tipo=EntidadAuditoriaAcceso.RECETA, entidad_id=receta_id)
        DetalleRecetaDialog(self._i18n, receta=receta, lineas=self._historial_base.detalle_por_receta.get(receta_id, ()), parent=self).exec()

    def _actualizar_acciones(self) -> None:
        self.btn_ver_informe.setEnabled(self._id_seleccionado(self.table_citas) is not None)
        self.btn_ver_detalle.setEnabled(self._id_seleccionado(self.table_recetas) is not None)

    def _id_seleccionado(self, tabla: QTableWidget) -> int | None:
        current = tabla.currentItem()
        if current is None:
            return None
        valor = tabla.item(current.row(), 0).data(Qt.ItemDataRole.UserRole)
        return int(valor) if valor is not None else None

    def _set_estado_cargando(self) -> None:
        self.lbl_estado.setText(self._i18n.t("historial.estado.cargando"))
        self.btn_ver_informe.setEnabled(False)
        self.btn_ver_detalle.setEnabled(False)
