from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.usecases.buscar_auditoria_accesos import BuscarAuditoriaAccesos
from clinicdesk.app.application.usecases.exportar_auditoria_csv import ExportacionAuditoriaDemasiadasFilasError, ExportacionAuditoriaError, ExportarAuditoriaCSV
from clinicdesk.app.application.usecases.filtros_auditoria import PRESET_PERSONALIZADO
from clinicdesk.app.application.usecases.obtener_resumen_auditoria import ObtenerResumenAuditoria
from clinicdesk.app.application.usecases.paginacion_incremental import calcular_siguiente_offset
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.auditoria.exportador_csv import ExportadorCsvAuditoria
from clinicdesk.app.pages.auditoria.filtros_ui import columnas_tabla, opciones_accion, opciones_entidad, opciones_rango, parse_fecha_iso
from clinicdesk.app.pages.shared.table_utils import set_item
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesosQueries, FiltrosAuditoriaAccesos

LOGGER = get_logger(__name__)


class PageAuditoria(QWidget):
    def __init__(self, connection, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._i18n = I18nManager("es")
        self._settings = QSettings("clinicdesk", "ui")
        self._queries = AuditoriaAccesosQueries(connection)
        self._uc_buscar = BuscarAuditoriaAccesos(self._queries)
        self._uc_resumen = ObtenerResumenAuditoria(self._queries)
        self._uc_exportar = ExportarAuditoriaCSV(self._queries)
        self._exportador = ExportadorCsvAuditoria(self, self._settings, self._tr)
        self._offset_actual, self._limit = 0, 50
        self._total_actual: int | None = None
        self._items_acumulados = []
        self._build_ui()
        self._retranslate()
        self._cargar_primera_pagina()

    def on_show(self) -> None:
        self._cargar_primera_pagina()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addLayout(self._build_resumen())
        root.addLayout(self._build_filtros())
        self.tabla = QTableWidget(0, 6)
        root.addWidget(self.tabla)
        pie = QHBoxLayout()
        self.lbl_estado = QLabel()
        self.btn_reintentar, self.btn_exportar, self.btn_cargar_mas = QPushButton(), QPushButton(), QPushButton()
        pie.addWidget(self.lbl_estado)
        pie.addWidget(self.btn_reintentar)
        pie.addStretch(1)
        pie.addWidget(self.btn_exportar)
        pie.addWidget(self.btn_cargar_mas)
        root.addLayout(pie)
        self.btn_buscar.clicked.connect(self._on_buscar)
        self.btn_limpiar.clicked.connect(self._on_limpiar)
        self.btn_reintentar.clicked.connect(self._on_reintentar)
        self.btn_cargar_mas.clicked.connect(self._on_cargar_mas)
        self.btn_exportar.clicked.connect(self._on_exportar)

    def _build_resumen(self) -> QGridLayout:
        grid = QGridLayout()
        self.lbl_accesos_hoy, self.lbl_accesos_7_dias, self.lbl_top_acciones = QLabel("0"), QLabel("0"), QLabel("-")
        grid.addWidget(QLabel(self._tr("auditoria.resumen.accesos_hoy")), 0, 0)
        grid.addWidget(self.lbl_accesos_hoy, 0, 1)
        grid.addWidget(QLabel(self._tr("auditoria.resumen.accesos_7_dias")), 0, 2)
        grid.addWidget(self.lbl_accesos_7_dias, 0, 3)
        grid.addWidget(QLabel(self._tr("auditoria.resumen.top_acciones")), 1, 0)
        grid.addWidget(self.lbl_top_acciones, 1, 1, 1, 3)
        return grid

    def _build_filtros(self) -> QHBoxLayout:
        filtros = QHBoxLayout()
        self.input_usuario, self.input_desde, self.input_hasta = QLineEdit(), QLineEdit(), QLineEdit()
        self.combo_rango, self.combo_accion, self.combo_entidad = QComboBox(), QComboBox(), QComboBox()
        self.btn_buscar, self.btn_limpiar = QPushButton(), QPushButton()
        for key, widget in (("auditoria.filtro.rango", self.combo_rango), ("auditoria.filtro.usuario", self.input_usuario), ("auditoria.filtro.accion", self.combo_accion), ("auditoria.filtro.entidad", self.combo_entidad), ("auditoria.filtro.desde", self.input_desde), ("auditoria.filtro.hasta", self.input_hasta)):
            filtros.addWidget(QLabel(self._tr(key)))
            filtros.addWidget(widget)
        filtros.addWidget(self.btn_buscar)
        filtros.addWidget(self.btn_limpiar)
        self.combo_rango.currentIndexChanged.connect(self._on_preset_cambiado)
        return filtros

    def _retranslate(self) -> None:
        self.btn_buscar.setText(self._tr("auditoria.accion.buscar"))
        self.btn_limpiar.setText(self._tr("auditoria.accion.limpiar"))
        self.btn_cargar_mas.setText(self._tr("auditoria.accion.cargar_mas"))
        self.btn_exportar.setText(self._tr("auditoria.accion.exportar_csv"))
        self.btn_reintentar.setText(self._tr("auditoria.accion.reintentar"))
        self.input_desde.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self.input_hasta.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self.tabla.setHorizontalHeaderLabels([self._tr(k) for k in columnas_tabla()])
        self._cargar_combos()
        self._set_estado("idle")

    def _cargar_combos(self) -> None:
        for combo, opciones in ((self.combo_rango, opciones_rango(self._tr)), (self.combo_accion, opciones_accion(self._tr)), (self.combo_entidad, opciones_entidad(self._tr))):
            combo.clear()
            for item in opciones:
                combo.addItem(item.texto, item.valor)

    def _on_preset_cambiado(self) -> None:
        personalizado = self.combo_rango.currentData() == PRESET_PERSONALIZADO
        self.input_desde.setEnabled(personalizado)
        self.input_hasta.setEnabled(personalizado)

    def _on_buscar(self) -> None:
        self._cargar_primera_pagina()

    def _on_limpiar(self) -> None:
        for control in (self.input_usuario, self.input_desde, self.input_hasta):
            control.clear()
        for combo in (self.combo_rango, self.combo_accion, self.combo_entidad):
            combo.setCurrentIndex(0)
        self._cargar_primera_pagina()

    def _on_reintentar(self) -> None:
        self._buscar(incremental=bool(self._items_acumulados))

    def _cargar_primera_pagina(self) -> None:
        self._items_acumulados, self._offset_actual, self._total_actual = [], 0, None
        self._buscar(incremental=False)

    def _on_cargar_mas(self) -> None:
        if self._total_actual is None or len(self._items_acumulados) >= self._total_actual:
            return
        LOGGER.info("auditoria_cargar_mas_click", extra={"action": "auditoria_cargar_mas_click"})
        self._buscar(incremental=True)

    def _buscar(self, *, incremental: bool) -> None:
        filtros = self._build_filtros()
        if filtros is None:
            return
        self._set_estado("loading_more" if incremental else "loading")
        try:
            resultado = self._uc_buscar.execute(filtros, self._limit, self._offset_actual, preset_rango=self.combo_rango.currentData(), total_conocido=self._total_actual)
            if not incremental:
                self._render_resumen(self._uc_resumen.execute(filtros.desde_utc, filtros.hasta_utc))
        except Exception:
            self._set_estado("error_more" if incremental and self._items_acumulados else "error")
            LOGGER.warning("auditoria_cargar_mas_fail", extra={"action": "auditoria_cargar_mas_fail"})
            return
        self._total_actual = resultado.total
        self._offset_actual = calcular_siguiente_offset(self._offset_actual, self._limit, resultado.total)
        if incremental:
            self._append_filas(resultado.items)
            LOGGER.info("auditoria_cargar_mas_ok", extra={"action": "auditoria_cargar_mas_ok"})
        else:
            self._items_acumulados = list(resultado.items)
            self._render_filas()
        self._set_estado("empty" if resultado.total == 0 else "ok")

    def _build_filtros(self) -> FiltrosAuditoriaAccesos | None:
        desde_texto, hasta_texto = self.input_desde.text().strip(), self.input_hasta.text().strip()
        desde, hasta = parse_fecha_iso(desde_texto), parse_fecha_iso(hasta_texto)
        if desde_texto and desde is None:
            return self._error_fecha(self._tr("auditoria.filtro.desde"))
        if hasta_texto and hasta is None:
            return self._error_fecha(self._tr("auditoria.filtro.hasta"))
        return FiltrosAuditoriaAccesos(
            usuario_contiene=self.input_usuario.text().strip() or None,
            accion=self.combo_accion.currentData(),
            entidad_tipo=self.combo_entidad.currentData(),
            desde_utc=desde,
            hasta_utc=hasta,
        )

    def _error_fecha(self, campo: str) -> None:
        QMessageBox.warning(self, self._tr("auditoria.titulo"), self._tr("auditoria.error.fecha_invalida").format(campo=campo))
        return None

    def _append_filas(self, items) -> None:
        scroll = self.tabla.verticalScrollBar()
        posicion = scroll.value()
        self._items_acumulados.extend(items)
        for indice, item in enumerate(items, self.tabla.rowCount()):
            self._insertar_fila(indice, item)
        scroll.setValue(posicion)

    def _render_filas(self) -> None:
        self.tabla.setRowCount(0)
        for row, item in enumerate(self._items_acumulados):
            self._insertar_fila(row, item)

    def _insertar_fila(self, row: int, item) -> None:
        self.tabla.insertRow(row)
        set_item(self.tabla, row, 0, item.timestamp_utc)
        set_item(self.tabla, row, 1, item.usuario)
        set_item(self.tabla, row, 2, self._tr("comun.si") if item.modo_demo else self._tr("comun.no"))
        set_item(self.tabla, row, 3, item.accion)
        set_item(self.tabla, row, 4, item.entidad_tipo)
        set_item(self.tabla, row, 5, item.entidad_id)

    def _set_estado(self, estado: str) -> None:
        mostrados, total = len(self._items_acumulados), self._total_actual or 0
        textos = {
            "loading": self._tr("auditoria.estado.cargando"),
            "loading_more": self._tr("auditoria.estado.cargando_mas"),
            "empty": self._tr("auditoria.estado.vacio"),
            "error": self._tr("auditoria.estado.error"),
            "error_more": self._tr("auditoria.estado.error_cargar_mas"),
            "ok": self._tr("auditoria.estado.mostrando_x_de_y").format(mostrados=mostrados, total=total),
            "idle": "",
        }
        self.lbl_estado.setText(textos[estado])
        self.btn_reintentar.setVisible(estado in {"error", "error_more"})
        self.btn_exportar.setEnabled(total > 0)
        self.btn_cargar_mas.setVisible(mostrados < total)
        self.btn_cargar_mas.setEnabled(estado == "ok" and mostrados < total)

    def _render_resumen(self, resumen) -> None:
        self.lbl_accesos_hoy.setText(str(resumen.accesos_hoy))
        self.lbl_accesos_7_dias.setText(str(resumen.accesos_ultimos_7_dias))
        top = [f"{item.accion} ({item.total})" for item in resumen.top_acciones]
        self.lbl_top_acciones.setText(", ".join(top) if top else self._tr("auditoria.resumen.sin_datos"))

    def _on_exportar(self) -> None:
        if not self._total_actual or not self._exportador.confirmar(self._total_actual):
            return
        filtros = self._build_filtros()
        if filtros is None:
            return
        try:
            exp = self._uc_exportar.execute(filtros, preset_rango=self.combo_rango.currentData())
        except (ExportacionAuditoriaDemasiadasFilasError, ExportacionAuditoriaError) as exc:
            self._exportador.mostrar_error(exc.reason_code, permitir_reintento=False)
            return
        self._exportador.guardar_con_reintento(exp.csv_texto, exp.filas, exp.nombre_archivo_sugerido, self.combo_rango.currentData())

    def _tr(self, key: str) -> str:
        return self._i18n.t(key)
