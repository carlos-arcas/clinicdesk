from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QTableWidgetItem, QWidget

from clinicdesk.app.application.confirmaciones import (
    FiltrosConfirmacionesDTO,
    ObtenerConfirmacionesCitas,
    PaginacionConfirmacionesDTO,
)
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria
from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.acciones_confirmaciones import navegar_prediccion
from clinicdesk.app.pages.confirmaciones.contratos_ui import ConfirmacionesUIRefs
from clinicdesk.app.pages.confirmaciones.filtros_confirmaciones_ui import (
    labels_columnas_confirmaciones,
    on_rango_changed,
    set_filter_options,
)
from clinicdesk.app.pages.confirmaciones.lote_controller import GestorLoteConfirmaciones
from clinicdesk.app.pages.confirmaciones.lote_worker import WorkerRecordatoriosLote
from clinicdesk.app.pages.confirmaciones.navegacion_confirmaciones import abrir_riesgo, ir_a_prediccion, render_banner
from clinicdesk.app.pages.confirmaciones.acciones_rapidas_confirmaciones import (
    on_whatsapp_rapido_fail,
    on_whatsapp_rapido_ok,
    preparar_whatsapp_rapido,
)
from clinicdesk.app.pages.confirmaciones.preferencias_confirmaciones import guardar_preferencias, restaurar_preferencias
from clinicdesk.app.pages.confirmaciones.render_confirmaciones import (
    apply_selection,
    render_estado,
    render_tabla,
)
from clinicdesk.app.pages.confirmaciones.seleccion_confirmaciones import (
    actualizar_cita_seleccionada,
    on_item_changed,
    toggle_todo_visible,
)
from clinicdesk.app.pages.confirmaciones.telemetria_confirmaciones import log_carga, registrar_telemetria
from clinicdesk.app.pages.confirmaciones.ui_builder import build_confirmaciones_ui
from clinicdesk.app.pages.confirmaciones.workers_confirmaciones import arrancar_busqueda_rapida, arrancar_carga
from clinicdesk.app.queries.confirmaciones_queries import ConfirmacionesQueries
from clinicdesk.app.ui.ux.error_feedback import presentar_error_recuperable
from clinicdesk.app.ui.ux.window_feedback import set_busy, toast_error, toast_info, toast_success
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EventoUI
from clinicdesk.app.ui.viewmodels.confirmaciones_vm import ConfirmacionesViewModel
from clinicdesk.app.ui.workers.listado_async_workers import CargaConfirmacionesWorker
from clinicdesk.app.infrastructure.sqlite.db_path import resolver_db_path_desde_conexion

_PAGE_SIZE = 20
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

    def _connect_signals(self) -> None:
        self._ui.btn_ir_prediccion.clicked.connect(self._ir_a_prediccion)
        self._ui.btn_actualizar.clicked.connect(lambda: self._load_data(reset=True))
        self._ui.cmb_rango.currentIndexChanged.connect(self._on_rango_changed)
        self._ui.cmb_riesgo.currentIndexChanged.connect(self._guardar_preferencias)
        self._ui.cmb_recordatorio.currentIndexChanged.connect(self._guardar_preferencias)
        self._ui.txt_buscar.editingFinished.connect(self._guardar_preferencias)
        self._ui.desde.dateChanged.connect(self._guardar_preferencias)
        self._ui.hasta.dateChanged.connect(self._guardar_preferencias)
        self._ui.chk_todo_visible.stateChanged.connect(self._toggle_todo_visible)
        self._ui.table.itemChanged.connect(self._on_item_changed)
        self._ui.btn_prev.clicked.connect(self._prev)
        self._ui.btn_next.clicked.connect(self._next)

    def on_show(self) -> None:
        if not self._preferencias_restauradas:
            self._restaurar_preferencias()
            self._preferencias_restauradas = True
        self._load_data(reset=True)

    def _retranslate(self) -> None:
        t = self._i18n.t
        self._ui.lbl_title.setText(t("confirmaciones.titulo"))
        self._ui.btn_ir_prediccion.setText(t("prediccion_ausencias.ir_a_prediccion"))
        self._ui.btn_actualizar.setText(t("confirmaciones.filtro.actualizar"))
        self._ui.btn_prev.setText(t("confirmaciones.paginacion.anterior"))
        self._ui.btn_next.setText(t("confirmaciones.paginacion.siguiente"))
        self._ui.txt_buscar.setPlaceholderText(t("confirmaciones.filtro.buscar"))
        self._ui.chk_todo_visible.setText(t("confirmaciones.seleccion.todo_visible"))
        self._lote.retranslate()
        set_filter_options(self._ui, self._i18n.t, self._on_rango_changed)
        self._ui.table.setHorizontalHeaderLabels(labels_columnas_confirmaciones(self._i18n.t))
        self._actualizar_estado_seleccion()

    def _on_rango_changed(self) -> None:
        on_rango_changed(self._ui)

    def _restaurar_preferencias(self) -> None:
        restaurar_preferencias(preferencias_service=self._container.preferencias_service, ui=self._ui)
        self._on_rango_changed()

    def _guardar_preferencias(self, *_args) -> None:
        guardar_preferencias(preferencias_service=self._container.preferencias_service, ui=self._ui)

    def _build_filtros(self, texto: str | None = None) -> FiltrosConfirmacionesDTO:
        return FiltrosConfirmacionesDTO(
            desde=self._ui.desde.date().toString("yyyy-MM-dd"),
            hasta=self._ui.hasta.date().toString("yyyy-MM-dd"),
            texto_paciente=texto if texto is not None else self._ui.txt_buscar.text(),
            recordatorio_filtro=str(self._ui.cmb_recordatorio.currentData()),
            riesgo_filtro=str(self._ui.cmb_riesgo.currentData()),
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
            rango=str(self._ui.cmb_rango.currentData()),
            estado=str(self._ui.cmb_recordatorio.currentData()),
            texto=self._ui.txt_buscar.text(),
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
            self._ui.table.setFocus()
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
        self._ui.lbl_totales.setText(
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
        self._vm.resolver_carga_error(error_key="ux_states.confirmaciones.error", emitir_toast=False)
        feedback = presentar_error_recuperable(error_type)
        toast_error(
            self,
            "toast.refresh_fail_retry",
            titulo_key=feedback.titulo_key,
            detalle=feedback.detalle,
            accion_label_key="toast.action.retry",
            accion_callback=self._refresh if hasattr(self, "_refresh") else (lambda: self._load_data(reset=True)),
            persistente=True,
        )

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
        toggle_todo_visible(
            self._ui.table, state, self._actualizar_cita_seleccionada, self._actualizar_estado_seleccion
        )

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        on_item_changed(
            item, self._actualizar_cita_seleccionada, self._vm.seleccionar, self._actualizar_estado_seleccion
        )

    def _actualizar_cita_seleccionada(self, item: QTableWidgetItem) -> None:
        actualizar_cita_seleccionada(item, self._citas_seleccionadas)

    def _actualizar_estado_seleccion(self) -> None:
        total = len(self._citas_seleccionadas)
        self._ui.lbl_seleccionadas.setText(self._i18n.t("confirmaciones.seleccion.contador").format(total=total))
        self._lote.actualizar_visibilidad(total)

    def _limpiar_seleccion(self) -> None:
        self._citas_seleccionadas.clear()
        self._ui.chk_todo_visible.setCheckState(Qt.Unchecked)
        self._actualizar_estado_seleccion()

    def _render_banner(self, estado: str) -> None:
        render_banner(self._ui, self._i18n.t, estado)

    def _abrir_riesgo(self, cita_id: int) -> None:
        abrir_riesgo(self, cita_id, self._registrar_telemetria)

    def _preparar_whatsapp_rapido(self, item) -> None:
        preparar_whatsapp_rapido(self, item)

    def _on_whatsapp_rapido_ok(self, _dto) -> None:
        on_whatsapp_rapido_ok(self)

    def _on_whatsapp_rapido_fail(self, reason_code: str) -> None:
        on_whatsapp_rapido_fail(self, reason_code)

    def _log_carga(self, reset: bool) -> None:
        log_carga(self, reset)

    def _registrar_telemetria(self, evento: str, resultado: str, cita_id: int | None) -> None:
        registrar_telemetria(self, evento, resultado, cita_id)

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
        ir_a_prediccion(self, navegar_prediccion)
