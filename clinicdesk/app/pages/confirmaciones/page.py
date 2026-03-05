from __future__ import annotations

import logging
from datetime import date, timedelta

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem, QWidget

from clinicdesk.app.application.confirmaciones import (
    FiltrosConfirmacionesDTO,
    ObtenerConfirmacionesCitas,
    PaginacionConfirmacionesDTO,
)
from clinicdesk.app.application.citas.filtros import redactar_texto_busqueda
from clinicdesk.app.application.prediccion_ausencias.aviso_salud_prediccion import (
    debe_mostrar_aviso_salud_prediccion,
)
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria
from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog
from clinicdesk.app.pages.confirmaciones.acciones_confirmaciones import (
    navegar_prediccion,
    set_busy,
    toast_error,
    toast_info,
    toast_success,
)
from clinicdesk.app.pages.confirmaciones.columnas import claves_columnas_confirmaciones
from clinicdesk.app.pages.confirmaciones.contratos_ui import ConfirmacionesUIRefs
from clinicdesk.app.pages.confirmaciones.lote_controller import GestorLoteConfirmaciones
from clinicdesk.app.pages.confirmaciones.lote_worker import AccionLoteDTO, WorkerRecordatoriosLote
from clinicdesk.app.pages.confirmaciones.preferencias_confirmaciones import guardar_preferencias, restaurar_preferencias
from clinicdesk.app.pages.confirmaciones.render_confirmaciones import (
    apply_selection,
    render_estado,
    render_tabla,
)
from clinicdesk.app.pages.confirmaciones.ui_builder import build_confirmaciones_ui
from clinicdesk.app.pages.confirmaciones.workers_confirmaciones import arrancar_busqueda_rapida, arrancar_carga
from clinicdesk.app.queries.confirmaciones_queries import ConfirmacionesQueries
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EventoUI
from clinicdesk.app.ui.viewmodels.confirmaciones_vm import ConfirmacionesViewModel
from clinicdesk.app.ui.workers.listado_async_workers import CargaConfirmacionesWorker
from clinicdesk.app.infrastructure.sqlite.db_path import resolver_db_path_desde_conexion

_PAGE_SIZE = 20
_COL_CHECK = 0
LOGGER = logging.getLogger(__name__)


class PageConfirmaciones(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._offset = 0
        self._total = 0
        self._citas_seleccionadas: set[int] = set()
        self._cita_en_preparacion: int | None = None
        self._uc_telemetria = RegistrarTelemetria(container.telemetria_eventos_repo)
        self._thread_rapido: QThread | None = None
        self._worker_rapido: WorkerRecordatoriosLote | None = None
        self._thread_carga: QThread | None = None
        self._worker_carga: CargaConfirmacionesWorker | None = None
        self._thread_busqueda_rapida: QThread | None = None
        self._token_carga = 0
        self._cita_focus_pendiente: int | None = None
        self._db_path = resolver_db_path_desde_conexion(container.connection)
        self._preferencias_restauradas = False
        self._vm = ConfirmacionesViewModel(listar_confirmaciones=self._listar_confirmaciones_sync)
        self._ui: ConfirmacionesUIRefs = build_confirmaciones_ui(self, i18n)
        self._wire_ui_aliases()
        self._lote = GestorLoteConfirmaciones(
            self,
            self._i18n,
            self._container.recordatorios_citas_facade,
            selected_ids=lambda: tuple(sorted(self._citas_seleccionadas)),
            on_done=lambda: self._load_data(reset=False),
        )
        self._ui.contenido_tabla.layout().insertWidget(1, self._lote.barra)
        self._connect_signals()
        self._vm.subscribe(self._on_estado_vm)
        self._vm.subscribe_eventos(self._on_evento_vm)
        self._i18n.subscribe(self._retranslate)
        self._retranslate()

    def _wire_ui_aliases(self) -> None:
        self.lbl_title = self._ui.lbl_title
        self.banner = self._ui.banner
        self.btn_ir_prediccion = self._ui.btn_ir_prediccion
        self.cmb_rango = self._ui.cmb_rango
        self.desde = self._ui.desde
        self.hasta = self._ui.hasta
        self.cmb_riesgo = self._ui.cmb_riesgo
        self.cmb_recordatorio = self._ui.cmb_recordatorio
        self.txt_buscar = self._ui.txt_buscar
        self.btn_actualizar = self._ui.btn_actualizar
        self.chk_todo_visible = self._ui.chk_todo_visible
        self.lbl_seleccionadas = self._ui.lbl_seleccionadas
        self.table = self._ui.table
        self.lbl_totales = self._ui.lbl_totales
        self.btn_prev = self._ui.btn_prev
        self.btn_next = self._ui.btn_next

    def _connect_signals(self) -> None:
        self.btn_ir_prediccion.clicked.connect(self._ir_a_prediccion)
        self.btn_actualizar.clicked.connect(lambda: self._load_data(reset=True))
        self.cmb_rango.currentIndexChanged.connect(self._on_rango_changed)
        self.cmb_riesgo.currentIndexChanged.connect(self._guardar_preferencias)
        self.cmb_recordatorio.currentIndexChanged.connect(self._guardar_preferencias)
        self.txt_buscar.editingFinished.connect(self._guardar_preferencias)
        self.desde.dateChanged.connect(self._guardar_preferencias)
        self.hasta.dateChanged.connect(self._guardar_preferencias)
        self.chk_todo_visible.stateChanged.connect(self._toggle_todo_visible)
        self.table.itemChanged.connect(self._on_item_changed)
        self.btn_prev.clicked.connect(self._prev)
        self.btn_next.clicked.connect(self._next)

    def on_show(self) -> None:
        if not self._preferencias_restauradas:
            self._restaurar_preferencias()
            self._preferencias_restauradas = True
        self._load_data(reset=True)

    def _retranslate(self) -> None:
        t = self._i18n.t
        self.lbl_title.setText(t("confirmaciones.titulo"))
        self.btn_ir_prediccion.setText(t("prediccion_ausencias.ir_a_prediccion"))
        self.btn_actualizar.setText(t("confirmaciones.filtro.actualizar"))
        self.btn_prev.setText(t("confirmaciones.paginacion.anterior"))
        self.btn_next.setText(t("confirmaciones.paginacion.siguiente"))
        self.txt_buscar.setPlaceholderText(t("confirmaciones.filtro.buscar"))
        self.chk_todo_visible.setText(t("confirmaciones.seleccion.todo_visible"))
        self._lote.retranslate()
        self._set_filter_options()
        self.table.setHorizontalHeaderLabels(self._labels_columnas())
        self._actualizar_estado_seleccion()

    def _labels_columnas(self) -> list[str]:
        mapa = {
            "seleccion": self._i18n.t("confirmaciones.seleccion.seleccionar"),
            "fecha": self._i18n.t("confirmaciones.col.fecha"),
            "hora": self._i18n.t("confirmaciones.col.hora"),
            "paciente": self._i18n.t("confirmaciones.col.paciente"),
            "medico": self._i18n.t("confirmaciones.col.medico"),
            "estado": self._i18n.t("confirmaciones.col.estado"),
            "riesgo": self._i18n.t("confirmaciones.col.riesgo"),
            "recordatorio": self._i18n.t("confirmaciones.col.recordatorio"),
            "acciones": self._i18n.t("confirmaciones.col.acciones"),
        }
        return [mapa[clave] for clave in claves_columnas_confirmaciones()]

    def _set_filter_options(self) -> None:
        t = self._i18n.t
        self.cmb_rango.clear()
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.hoy"), "HOY")
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.7d"), "7D")
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.30d"), "30D")
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.custom"), "CUSTOM")
        self.cmb_riesgo.clear()
        self.cmb_riesgo.addItem(t("confirmaciones.filtro.riesgo.todos"), "TODOS")
        self.cmb_riesgo.addItem(t("confirmaciones.filtro.riesgo.alto_medio"), "ALTO_MEDIO")
        self.cmb_riesgo.addItem(t("confirmaciones.filtro.riesgo.solo_alto"), "SOLO_ALTO")
        self.cmb_recordatorio.clear()
        self.cmb_recordatorio.addItem(t("confirmaciones.filtro.recordatorio.todos"), "TODOS")
        self.cmb_recordatorio.addItem(t("confirmaciones.filtro.recordatorio.sin_preparar"), "SIN_PREPARAR")
        self.cmb_recordatorio.addItem(t("confirmaciones.filtro.recordatorio.no_enviado"), "NO_ENVIADO")
        self._on_rango_changed()

    def _on_rango_changed(self) -> None:
        mode = self.cmb_rango.currentData()
        today = date.today()
        end = today if mode == "HOY" else today + timedelta(days=30 if mode == "30D" else 7)
        if mode != "CUSTOM":
            self.desde.setDate(today)
            self.hasta.setDate(end)
        self.desde.setEnabled(mode == "CUSTOM")
        self.hasta.setEnabled(mode == "CUSTOM")

    def _restaurar_preferencias(self) -> None:
        restaurar_preferencias(preferencias_service=self._container.preferencias_service, ui=self._ui)
        self._on_rango_changed()

    def _guardar_preferencias(self, *_args) -> None:
        guardar_preferencias(preferencias_service=self._container.preferencias_service, ui=self._ui)

    def _build_filtros(self, texto: str | None = None) -> FiltrosConfirmacionesDTO:
        return FiltrosConfirmacionesDTO(
            desde=self.desde.date().toString("yyyy-MM-dd"),
            hasta=self.hasta.date().toString("yyyy-MM-dd"),
            texto_paciente=texto if texto is not None else self.txt_buscar.text(),
            recordatorio_filtro=str(self.cmb_recordatorio.currentData()),
            riesgo_filtro=str(self.cmb_riesgo.currentData()),
        )

    def _load_data(self, *, reset: bool) -> None:
        self._guardar_preferencias()
        self._token_carga += 1
        token = self._token_carga
        if reset:
            self._offset = 0
        self._log_carga(reset)
        self._limpiar_seleccion()
        self._vm.actualizar_contexto(
            rango=str(self.cmb_rango.currentData()),
            estado=str(self.cmb_recordatorio.currentData()),
            texto=self.txt_buscar.text(),
        )
        self._vm.set_loading()
        set_busy(self, True, "busy.loading_confirmaciones")
        self._arrancar_worker_carga(token=token)

    def refrescar_desde_atajo(self) -> None:
        self._load_data(reset=True)

    def buscar_rapido_async(self, texto: str, on_done) -> None:
        if self._thread_busqueda_rapida is not None and self._thread_busqueda_rapida.isRunning():
            return
        self._thread_busqueda_rapida = arrancar_busqueda_rapida(
            owner=self,
            db_path=self._db_path,
            filtros=self._build_filtros(texto),
            page_size=_PAGE_SIZE,
            riesgo_uc=self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc,
            salud_uc=self._container.prediccion_ausencias_facade.obtener_salud_uc,
            on_payload=lambda result: on_done(result.items),
            on_thread_finished=self._reset_thread_busqueda_rapida,
        )

    def _reset_thread_busqueda_rapida(self) -> None:
        self._thread_busqueda_rapida = None

    def seleccionar_cita_desde_busqueda(self, cita_id: int) -> None:
        if apply_selection(self._ui, cita_id):
            self.table.setFocus()
            self._vm.seleccionar(cita_id)
            return
        self._cita_focus_pendiente = cita_id
        self._load_data(reset=True)

    def _arrancar_worker_carga(self, *, token: int) -> None:
        if self._thread_carga is not None and self._thread_carga.isRunning():
            return
        self._thread_carga, self._worker_carga = arrancar_carga(
            owner=self,
            db_path=self._db_path,
            filtros=self._build_filtros(),
            page_size=_PAGE_SIZE,
            offset=self._offset,
            riesgo_uc=self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc,
            salud_uc=self._container.prediccion_ausencias_facade.obtener_salud_uc,
            on_ok=lambda result: self._on_carga_ok(result, token),
            on_error=lambda error: self._on_carga_error(error, token),
            on_thread_finished=self._reset_worker_carga,
        )

    def _reset_worker_carga(self) -> None:
        self._thread_carga = None
        self._worker_carga = None

    def _on_carga_ok(self, result, token: int) -> None:
        if token != self._token_carga:
            return
        set_busy(self, False, "busy.loading_confirmaciones")
        self._total = result.total
        self._render_banner(result.salud_prediccion.estado if result.salud_prediccion else "ROJO")
        self.lbl_totales.setText(
            self._i18n.t("confirmaciones.paginacion.mostrando").format(mostrados=result.mostrados, total=result.total)
        )
        if self._cita_focus_pendiente is not None:
            self._vm.seleccionar(self._cita_focus_pendiente)
            self._cita_focus_pendiente = None
        self._vm.resolver_carga_ok(rows=result.items, emitir_toast=True)

    def _on_carga_error(self, error_type: str, token: int) -> None:
        if token != self._token_carga:
            return
        set_busy(self, False, "busy.loading_confirmaciones")
        LOGGER.warning(
            "confirmaciones_carga_error", extra={"action": "confirmaciones_carga_error", "error": error_type}
        )
        self._vm.resolver_carga_error(error_key="ux_states.confirmaciones.error", emitir_toast=True)

    def _on_estado_vm(self, estado: EstadoListado[object]) -> None:
        render_estado(self._ui, estado, on_retry=lambda: self._load_data(reset=True), render_rows=self._render_rows)

    def _on_evento_vm(self, evento: EventoUI) -> None:
        if evento.tipo == "nav":
            cita_id = evento.payload.get("cita_id")
            if isinstance(cita_id, int):
                self.seleccionar_cita_desde_busqueda(cita_id)
            return
        if evento.tipo != "toast":
            return
        key = evento.payload.get("key")
        if not isinstance(key, str):
            return
        if key == "toast.refresh_fail":
            toast_error(self, key)
        elif key == "toast.refresh_empty_confirmaciones":
            toast_info(self, key)
        else:
            toast_success(self, key)

    def _render_rows(self, rows: list[object]) -> None:
        render_tabla(
            ui=self._ui,
            rows=rows,
            seleccionadas=self._citas_seleccionadas,
            cita_en_preparacion=self._cita_en_preparacion,
            traducir=self._i18n.t,
            on_abrir_riesgo=self._abrir_riesgo,
            on_preparar_whatsapp=self._preparar_whatsapp_rapido,
        )
        if self._vm.estado.seleccion_id is not None:
            apply_selection(self._ui, self._vm.estado.seleccion_id)
        self._actualizar_estado_seleccion()

    def _toggle_todo_visible(self, state: int) -> None:
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, _COL_CHECK)
            if item is not None:
                item.setCheckState(check_state)
                self._actualizar_cita_seleccionada(item)
        self.table.blockSignals(False)
        self._actualizar_estado_seleccion()

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != _COL_CHECK:
            return
        self._actualizar_cita_seleccionada(item)
        cita_id = item.data(Qt.UserRole)
        if isinstance(cita_id, int) and item.checkState() == Qt.Checked:
            self._vm.seleccionar(cita_id)
        self._actualizar_estado_seleccion()

    def _actualizar_cita_seleccionada(self, item: QTableWidgetItem) -> None:
        cita_id = item.data(Qt.UserRole)
        if not isinstance(cita_id, int):
            return
        if item.checkState() == Qt.Checked:
            self._citas_seleccionadas.add(cita_id)
            return
        self._citas_seleccionadas.discard(cita_id)

    def _actualizar_estado_seleccion(self) -> None:
        total = len(self._citas_seleccionadas)
        self.lbl_seleccionadas.setText(self._i18n.t("confirmaciones.seleccion.contador").format(total=total))
        self._lote.actualizar_visibilidad(total)

    def _limpiar_seleccion(self) -> None:
        self._citas_seleccionadas.clear()
        self.chk_todo_visible.setCheckState(Qt.Unchecked)
        self._actualizar_estado_seleccion()

    def _render_banner(self, estado: str) -> None:
        mostrar = debe_mostrar_aviso_salud_prediccion(True, estado)
        self.banner.setText(self._i18n.t("prediccion_ausencias.aviso_salud_prediccion") if mostrar else "")
        self.banner.setVisible(mostrar)
        self.btn_ir_prediccion.setVisible(mostrar)

    def _abrir_riesgo(self, cita_id: int) -> None:
        explicacion = self._container.prediccion_ausencias_facade.obtener_explicacion_riesgo_uc.ejecutar(cita_id)
        salud = self._container.prediccion_ausencias_facade.obtener_salud_uc.ejecutar()
        RiesgoAusenciaDialog(self._i18n, explicacion, salud, self).exec()
        self._registrar_telemetria("explicacion_ver_por_que", "ok", cita_id)

    def _preparar_whatsapp_rapido(self, item) -> None:
        if self._cita_en_preparacion is not None:
            return
        self._cita_en_preparacion = item.cita_id
        self._load_data(reset=False)
        self._registrar_telemetria("confirmaciones_whatsapp_rapido", "click", item.cita_id)
        self._thread_rapido = QThread(self)
        accion = AccionLoteDTO(tipo="PREPARAR", cita_ids=(item.cita_id,), canal="WHATSAPP")
        self._worker_rapido = WorkerRecordatoriosLote(self._container.recordatorios_citas_facade, accion)
        self._worker_rapido.moveToThread(self._thread_rapido)
        self._thread_rapido.started.connect(self._worker_rapido.run)
        self._worker_rapido.finished_ok.connect(self._on_whatsapp_rapido_ok)
        self._worker_rapido.finished_error.connect(self._on_whatsapp_rapido_fail)
        self._worker_rapido.finished.connect(self._thread_rapido.quit)
        self._worker_rapido.finished.connect(self._worker_rapido.deleteLater)
        self._thread_rapido.finished.connect(self._thread_rapido.deleteLater)
        self._thread_rapido.start()

    def _on_whatsapp_rapido_ok(self, _dto) -> None:
        self._registrar_telemetria("confirmaciones_whatsapp_rapido", "ok", self._cita_en_preparacion)
        self._cita_en_preparacion = None
        self._load_data(reset=False)
        QMessageBox.information(
            self, self._i18n.t("confirmaciones.titulo"), self._i18n.t("confirmaciones.accion.hecho")
        )

    def _on_whatsapp_rapido_fail(self, reason_code: str) -> None:
        LOGGER.warning(
            "confirmaciones_whatsapp_rapido_fail",
            extra={"action": "confirmaciones_whatsapp_rapido_fail", "reason_code": reason_code},
        )
        self._registrar_telemetria("confirmaciones_whatsapp_rapido", "fail", self._cita_en_preparacion)
        self._cita_en_preparacion = None
        self._load_data(reset=False)
        QMessageBox.warning(
            self,
            self._i18n.t("confirmaciones.titulo"),
            self._i18n.t("confirmaciones.accion.error_guardar"),
        )

    def _log_carga(self, reset: bool) -> None:
        LOGGER.info(
            "confirmaciones_carga",
            extra={
                "action": "confirmaciones_carga",
                "reset": reset,
                "offset": self._offset,
                "texto_redactado": redactar_texto_busqueda(self.txt_buscar.text()),
                "riesgo_filtro": str(self.cmb_riesgo.currentData()),
                "recordatorio_filtro": str(self.cmb_recordatorio.currentData()),
            },
        )

    def _registrar_telemetria(self, evento: str, resultado: str, cita_id: int | None) -> None:
        try:
            self._uc_telemetria.ejecutar(
                contexto_usuario=self._container.user_context,
                evento=evento,
                contexto=f"page=confirmaciones;resultado={resultado}",
                entidad_tipo="cita",
                entidad_id=cita_id,
            )
        except Exception:
            return

    def _listar_confirmaciones_sync(self, **kwargs) -> list[object]:
        use_case = ObtenerConfirmacionesCitas(
            queries=ConfirmacionesQueries(self._container.connection),
            obtener_riesgo_uc=self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc,
            obtener_salud_uc=self._container.prediccion_ausencias_facade.obtener_salud_uc,
        )
        filtros = self._build_filtros(kwargs.get("filtro_texto"))
        result = use_case.ejecutar(filtros, PaginacionConfirmacionesDTO(limit=_PAGE_SIZE, offset=0))
        return list(result.items)

    def _prev(self) -> None:
        self._offset = max(0, self._offset - _PAGE_SIZE)
        self._load_data(reset=False)

    def _next(self) -> None:
        if self._offset + _PAGE_SIZE >= self._total:
            return
        self._offset += _PAGE_SIZE
        self._load_data(reset=False)

    def _ir_a_prediccion(self) -> None:
        LOGGER.info(
            "aviso_salud_prediccion_cta", extra={"action": "aviso_salud_prediccion_cta", "page": "confirmaciones"}
        )
        navegar_prediccion(self)
