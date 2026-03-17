from __future__ import annotations

from typing import Optional
from time import perf_counter

import logging

from PySide6.QtCore import QThread, QTimer, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.application.usecases.pacientes_crud import (
    CrearPacienteUseCase,
    DesactivarPacienteUseCase,
    EditarPacienteUseCase,
)
from clinicdesk.app.application.services.pacientes_listado_contrato import ContratoListadoPacientesService
from clinicdesk.app.application.usecases.obtener_detalle_cita import ObtenerDetalleCita
from clinicdesk.app.application.historial_paciente import (
    BuscarHistorialCitasPaciente,
    BuscarHistorialRecetasPaciente,
    ObtenerResumenHistorialPaciente,
)
from clinicdesk.app.application.usecases.obtener_historial_paciente import ObtenerHistorialPaciente
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import RegistrarAuditoriaAcceso
from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.pages.pacientes.acciones_pacientes import (
    on_desactivar,
    on_editar,
    on_historial,
    on_nuevo,
    open_context_menu,
    open_csv_dialog,
)
from clinicdesk.app.pages.pacientes.coordinador_carga import CoordinadorCargaPacientes, SolicitudCargaPacientes
from clinicdesk.app.pages.pacientes.preferencias_pacientes import guardar_preferencias, restaurar_preferencias
from clinicdesk.app.pages.pacientes.render_pacientes import (
    apply_selection,
    render_estado,
    render_tabla,
    selected_id as obtener_selected_id,
    update_action_buttons,
)
from clinicdesk.app.ui.ux.error_feedback import presentar_error_recuperable
from clinicdesk.app.pages.pacientes.window_feedback import set_busy, toast_error, toast_success
from clinicdesk.app.pages.pacientes.workers_pacientes import (
    RelayBusquedaRapidaPacientes,
    RelayCargaPacientes,
    arrancar_busqueda_rapida,
    arrancar_carga,
)
from clinicdesk.app.pages.pacientes.ui_builder import build_pacientes_ui
from clinicdesk.app.pages.shared.contexto_tabla import (
    ContextoTablaListado,
    capturar_contexto_tabla,
    restaurar_contexto_tabla,
)
from clinicdesk.app.pages.shared.crud_page_helpers import set_buttons_enabled
from clinicdesk.app.queries.historial_paciente_queries import HistorialPacienteQueries
from clinicdesk.app.queries.historial_listados_queries import HistorialListadosQueries
from clinicdesk.app.queries.pacientes_queries import PacienteRow, PacientesQueries
from clinicdesk.app.queries.recetas_queries import RecetasQueries
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla, EventoUI
from clinicdesk.app.ui.viewmodels.pacientes_vm import PacientesViewModel
from clinicdesk.app.infrastructure.sqlite.db_path import resolver_db_path_desde_conexion
from clinicdesk.app.ui.workers.listado_async_workers import CargaPacientesWorker


LOGGER = logging.getLogger(__name__)


class PagePacientes(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._db_path = resolver_db_path_desde_conexion(container.connection)
        self._can_write = container.user_context.can_write
        self._uc_crear = CrearPacienteUseCase(container.pacientes_repo, container.user_context)
        self._uc_editar = EditarPacienteUseCase(container.pacientes_repo, container.user_context)
        self._uc_desactivar = DesactivarPacienteUseCase(container.pacientes_repo, container.user_context)
        self._i18n = I18nManager("es")
        self._contrato_listado = ContratoListadoPacientesService()
        self._columnas = self._contrato_listado.atributos_disponibles()
        self._uc_historial = ObtenerHistorialPaciente(
            pacientes_gateway=container.pacientes_repo,
            citas_gateway=HistorialPacienteQueries(container.connection),
            recetas_gateway=RecetasQueries(container.connection),
        )

        self._uc_detalle_cita = ObtenerDetalleCita(HistorialPacienteQueries(container.connection))
        historial_queries = HistorialListadosQueries(container.connection)
        self._uc_buscar_historial_citas = BuscarHistorialCitasPaciente(historial_queries)
        self._uc_buscar_historial_recetas = BuscarHistorialRecetasPaciente(historial_queries)
        self._uc_resumen_historial = ObtenerResumenHistorialPaciente(historial_queries)
        self._uc_auditoria_acceso = RegistrarAuditoriaAcceso(container.auditoria_accesos_repo)
        self._thread_carga: QThread | None = None
        self._worker_carga: CargaPacientesWorker | None = None
        self._relay_carga: RelayCargaPacientes | None = None
        self._token_carga = 0
        self._coordinador_carga = CoordinadorCargaPacientes()
        self._inicio_cargas: dict[int, float] = {}
        self._thread_busqueda_rapida: QThread | None = None
        self._worker_busqueda_rapida: CargaPacientesWorker | None = None
        self._relay_busqueda_rapida: RelayBusquedaRapidaPacientes | None = None
        self._token_busqueda_rapida = 0
        self._on_done_busqueda_rapida = None
        self._preferencias_restauradas = False
        self._refresh_diferido_pendiente = False
        self._token_on_show = 0
        self._token_refresh_programado = 0
        self._pagina_visible = False
        self._contexto_tabla_pendiente = ContextoTablaListado(fila_id=None, scroll_vertical=0, mantener_foco=False)
        self._vm = PacientesViewModel(listar_pacientes=self._listar_pacientes_sync)

        self._ui = build_pacientes_ui(
            self,
            self._i18n,
            can_write=self._can_write,
            headers=[self._i18n.t(col.clave_i18n) for col in self._columnas],
        )
        self.filtros = self._ui.filtros
        self.table = self._ui.table
        self.btn_nuevo = self._ui.btn_nuevo
        self.btn_editar = self._ui.btn_editar
        self.btn_desactivar = self._ui.btn_desactivar
        self.btn_historial = self._ui.btn_historial
        self.btn_csv = self._ui.btn_csv
        self._connect_signals()
        self._build_shortcuts()
        self._vm.subscribe(self._on_estado_vm)
        self._vm.subscribe_eventos(self._on_evento_vm)

    def _build_shortcuts(self) -> None:
        self._shortcut_focus_busqueda = QShortcut(QKeySequence("Ctrl+F"), self)
        self._shortcut_focus_busqueda.activated.connect(self.filtros.txt_busqueda.setFocus)
        self._shortcut_limpiar_filtros = QShortcut(QKeySequence("Ctrl+L"), self)
        self._shortcut_limpiar_filtros.activated.connect(self._atajo_limpiar_filtros)

    def _atajo_limpiar_filtros(self) -> None:
        self._reset_filters()
        self._refresh()

    def _connect_signals(self) -> None:
        self.filtros.filtros_cambiados.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda _: self._on_historial())
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_desactivar.clicked.connect(self._on_desactivar)
        self.btn_historial.clicked.connect(self._on_historial)
        self.btn_csv.clicked.connect(self._open_csv_dialog)

    def on_show(self) -> None:
        self._pagina_visible = True
        self._token_on_show += 1
        if not self._preferencias_restauradas:
            self._restaurar_preferencias()
            self._preferencias_restauradas = True
            self.filtros.txt_busqueda.setFocus()
        self._programar_refresh_on_show(self._token_on_show)

    def on_hide(self) -> None:
        self._pagina_visible = False

    def _programar_refresh_on_show(self, token_on_show: int) -> None:
        self._token_refresh_programado = token_on_show
        if self._refresh_diferido_pendiente:
            return
        self._refresh_diferido_pendiente = True
        QTimer.singleShot(0, self._ejecutar_refresh_diferido)

    def _ejecutar_refresh_diferido(self) -> None:
        self._refresh_diferido_pendiente = False
        if self._token_refresh_programado != self._token_on_show:
            LOGGER.info(
                "pacientes_refresh_omitido",
                extra={
                    "action": "pacientes_refresh_omitido",
                    "reason": "on_show_obsoleto",
                    "token_on_show": self._token_on_show,
                },
            )
            return
        if not self._pagina_visible:
            LOGGER.info(
                "pacientes_refresh_omitido",
                extra={
                    "action": "pacientes_refresh_omitido",
                    "reason": "pagina_no_visible",
                    "token_on_show": self._token_on_show,
                },
            )
            return
        self._refresh()

    def _refresh(self) -> None:
        self._guardar_preferencias()
        self._contexto_tabla_pendiente = capturar_contexto_tabla(self.table, columna_id=0)
        self._token_carga += 1
        token = self._token_carga
        selected_id = obtener_selected_id(self._ui)
        activo = self.filtros.activo()
        texto = normalize_search_text(self.filtros.texto())
        self._vm.actualizar_contexto(activo=activo, texto=texto, seleccion_id=selected_id)
        if self._vm.estado.estado_pantalla is not EstadoPantalla.LOADING:
            self._vm.set_loading()
        set_busy(self, True, "busy.loading_pacientes")
        solicitud = SolicitudCargaPacientes(token=token, seleccion_id=selected_id, activo=activo, texto=texto)
        if self._coordinador_carga.registrar(solicitud):
            self._arrancar_worker_carga(solicitud)
            return
        LOGGER.info(
            "pacientes_carga_reprogramada",
            extra={"action": "pacientes_carga_reprogramada", "token": token, "activo": activo, "has_text": bool(texto)},
        )

    def refrescar_desde_atajo(self) -> None:
        self._refresh()

    def atajo_nuevo(self) -> None:
        if self._can_write:
            self._on_nuevo()

    def _restaurar_preferencias(self) -> None:
        restaurar_preferencias(preferencias_service=self._container.preferencias_service, filtros_widget=self.filtros)

    def _guardar_preferencias(self) -> None:
        guardar_preferencias(preferencias_service=self._container.preferencias_service, filtros_widget=self.filtros)

    def buscar_rapido_async(self, texto: str, on_done) -> None:
        if self._thread_busqueda_rapida is not None and self._thread_busqueda_rapida.isRunning():
            return
        self._token_busqueda_rapida += 1
        token = self._token_busqueda_rapida
        self._on_done_busqueda_rapida = on_done
        self._thread_busqueda_rapida, self._worker_busqueda_rapida, self._relay_busqueda_rapida = (
            arrancar_busqueda_rapida(
                owner=self,
                db_path=self._db_path,
                activo=self.filtros.activo(),
                texto=normalize_search_text(texto),
                token=token,
                on_payload=self._on_busqueda_rapida_ok,
                on_error=self._on_busqueda_rapida_error,
                on_thread_finished=self._on_busqueda_rapida_thread_finished,
            )
        )

    @Slot(int)
    def _on_busqueda_rapida_thread_finished(self, _token: int) -> None:
        self._reset_thread_busqueda_rapida()

    @Slot(object, int)
    def _on_busqueda_rapida_ok(self, payload: object, token: int) -> None:
        if token != self._token_busqueda_rapida:
            LOGGER.info(
                "pacientes_busqueda_rapida_omitida",
                extra={"action": "pacientes_busqueda_rapida_omitida", "reason": "token_obsoleto", "token": token},
            )
            return
        if not self._pagina_visible:
            LOGGER.info(
                "pacientes_busqueda_rapida_omitida",
                extra={"action": "pacientes_busqueda_rapida_omitida", "reason": "pagina_no_visible", "token": token},
            )
            return
        on_done = getattr(self, "_on_done_busqueda_rapida", None)
        if not callable(on_done):
            return
        if not isinstance(payload, dict):
            on_done([])
            return
        rows = payload.get("rows", [])
        on_done(rows)

    @Slot(str, int)
    def _on_busqueda_rapida_error(self, error_type: str, token: int) -> None:
        if token != self._token_busqueda_rapida:
            return
        LOGGER.warning(
            "pacientes_busqueda_rapida_error",
            extra={"action": "pacientes_busqueda_rapida_error", "error": error_type, "token": token},
        )

    def _reset_thread_busqueda_rapida(self) -> None:
        self._thread_busqueda_rapida = None
        self._worker_busqueda_rapida = None
        self._relay_busqueda_rapida = None

    def seleccionar_paciente_desde_busqueda(self, paciente: PacienteRow) -> None:
        self._select_by_id(paciente.id)
        self.table.setFocus()

    def _arrancar_worker_carga(self, solicitud: SolicitudCargaPacientes) -> None:
        self._inicio_cargas[solicitud.token] = perf_counter()
        LOGGER.info(
            "pacientes_carga_inicio",
            extra={
                "action": "pacientes_carga_inicio",
                "token": solicitud.token,
                "activo": solicitud.activo,
                "has_text": bool(solicitud.texto),
            },
        )
        self._thread_carga, self._worker_carga, self._relay_carga = arrancar_carga(
            owner=self,
            db_path=self._db_path,
            activo=solicitud.activo,
            texto=solicitud.texto,
            token=solicitud.token,
            seleccion_id=solicitud.seleccion_id,
            on_ok=self._on_carga_ok,
            on_error=self._on_carga_error,
            on_thread_finished=self._on_carga_thread_finished,
        )

    @Slot(int)
    def _on_carga_thread_finished(self, token: int) -> None:
        self._thread_carga = None
        self._worker_carga = None
        self._relay_carga = None
        siguiente = self._coordinador_carga.finalizar(token)
        if siguiente is None:
            return
        self._arrancar_worker_carga(siguiente)

    @Slot(object, int, object)
    def _on_carga_ok(self, payload: object, token: int, selected_id: object) -> None:
        selected_id_int = selected_id if isinstance(selected_id, int) else None
        if token != self._token_carga or not self._coordinador_carga.es_token_activo(token):
            LOGGER.info(
                "pacientes_carga_omitida",
                extra={"action": "pacientes_carga_omitida", "reason": "token_obsoleto", "token": token},
            )
            return
        if not isinstance(payload, dict):
            LOGGER.warning(
                "pacientes_carga_omitida",
                extra={"action": "pacientes_carga_omitida", "reason": "payload_invalido", "token": token},
            )
            return
        if not self._pagina_visible:
            LOGGER.info(
                "pacientes_carga_omitida",
                extra={
                    "action": "pacientes_carga_omitida",
                    "reason": "pagina_no_visible",
                    "token": token,
                    "fase": "ok",
                },
            )
            return
        set_busy(self, False, "busy.loading_pacientes")
        rows = payload.get("rows", [])
        total_base = int(payload.get("total_base", len(rows)))
        inicio = self._inicio_cargas.pop(token, None)
        duracion_ms = int((perf_counter() - inicio) * 1000) if inicio else None
        LOGGER.info(
            "pacientes_carga_ok",
            extra={
                "action": "pacientes_carga_ok",
                "token": token,
                "rows": len(rows),
                "total_base": total_base,
                "duracion_ms": duracion_ms,
            },
        )
        self.filtros.set_contador(len(rows), total_base)
        self._vm.seleccionar(selected_id_int)
        self._vm.resolver_carga_ok(rows=rows, emitir_toast=True)
        restaurar_contexto_tabla(self.table, self._contexto_tabla_pendiente, columna_id=0)
        if rows:
            self.table.setFocus()

    @Slot(str, int)
    def _on_carga_error(self, error_type: str, token: int) -> None:
        if token != self._token_carga or not self._coordinador_carga.es_token_activo(token):
            LOGGER.info(
                "pacientes_carga_omitida",
                extra={"action": "pacientes_carga_omitida", "reason": "token_obsoleto", "token": token},
            )
            return
        if not self._pagina_visible:
            LOGGER.info(
                "pacientes_carga_omitida",
                extra={
                    "action": "pacientes_carga_omitida",
                    "reason": "pagina_no_visible",
                    "token": token,
                    "fase": "error",
                    "error": error_type,
                },
            )
            return
        set_busy(self, False, "busy.loading_pacientes")
        inicio = self._inicio_cargas.pop(token, None)
        duracion_ms = int((perf_counter() - inicio) * 1000) if inicio else None
        LOGGER.warning(
            "pacientes_carga_error",
            extra={
                "action": "pacientes_carga_error",
                "token": token,
                "error": error_type,
                "duracion_ms": duracion_ms,
            },
        )
        self._vm.resolver_carga_error(error_key="ux_states.pacientes.error", emitir_toast=False)
        feedback = presentar_error_recuperable(error_type)
        toast_error(
            self,
            "toast.refresh_fail_retry",
            titulo_key=feedback.titulo_key,
            detalle=feedback.detalle,
            accion_label_key="toast.action.retry",
            accion_callback=self._refresh,
            persistente=True,
        )

    def _on_estado_vm(self, estado: EstadoListado[PacienteRow]) -> None:
        LOGGER.debug(
            "pacientes_estado_render",
            extra={
                "action": "pacientes_estado_render",
                "token": self._token_carga,
                "fase": estado.estado_pantalla.name,
                "visible": self._pagina_visible,
            },
        )
        if not self._pagina_visible:
            LOGGER.info(
                "pacientes_estado_omitido",
                extra={
                    "action": "pacientes_estado_omitido",
                    "token": self._token_carga,
                    "fase": estado.estado_pantalla.name,
                    "visible": self._pagina_visible,
                },
            )
            return
        render_estado(
            self._ui,
            estado,
            on_retry=self._refresh,
            render_rows=self._render,
            apply_selected_id=self._select_by_id,
            update_buttons=self._update_buttons,
        )

    def _on_evento_vm(self, evento: EventoUI) -> None:
        if evento.tipo != "toast":
            return
        key = evento.payload.get("key")
        if not isinstance(key, str):
            return
        if key == "toast.refresh_fail":
            toast_error(self, key)
            return
        toast_success(self, key)

    def _listar_pacientes_sync(self, activo: bool, texto: str) -> list[PacienteRow]:
        queries = PacientesQueries(self._container.connection)
        base_rows = queries.list_all(activo=activo)
        if not texto:
            return base_rows
        return queries.search(texto=texto, activo=activo)

    def _render(self, rows: list[PacienteRow]) -> None:
        render_tabla(
            self._ui,
            rows,
            columnas=list(self._columnas),
            obtener_valor_columna=self._valor_columna,
            obtener_tooltip=self._tooltip_mascarado,
            formatear_valor_listado=self._contrato_listado.formatear_valor_listado,
        )

    def _valor_columna(self, paciente: PacienteRow, nombre_columna: str) -> object:
        if nombre_columna == "activo":
            return self._i18n.t("comun.si") if paciente.activo else self._i18n.t("comun.no")
        return getattr(paciente, nombre_columna, "")

    def _tooltip_mascarado(self, paciente: PacienteRow) -> str:
        documento = self._contrato_listado.formatear_valor_listado("documento", paciente.documento)
        telefono = self._contrato_listado.formatear_valor_listado("telefono", paciente.telefono)
        estado = self._i18n.t("comun.si") if paciente.activo else self._i18n.t("comun.no")
        return self._i18n.t("pacientes.tooltip.listado").format(documento=documento, telefono=telefono, estado=estado)

    def _update_buttons(self) -> None:
        update_action_buttons(self._ui, can_write=self._can_write, set_buttons_enabled=set_buttons_enabled)

    def _on_nuevo(self) -> None:
        on_nuevo(parent=self, i18n=self._i18n, uc_crear=self._uc_crear, on_success=self._on_nuevo_ok)

    def _on_nuevo_ok(self) -> None:
        self._reset_filters()
        self._refresh()

    def _on_editar(self) -> None:
        on_editar(
            parent=self,
            selected_id=obtener_selected_id(self._ui),
            obtener_paciente=self._container.pacientes_repo.get_by_id,
            uc_editar=self._uc_editar,
            i18n=self._i18n,
            on_success=self._refresh,
        )

    def _on_desactivar(self) -> None:
        on_desactivar(
            parent=self,
            selected_id=obtener_selected_id(self._ui),
            uc_desactivar=self._uc_desactivar,
            on_success=self._refresh,
        )

    def _select_by_id(self, paciente_id: int) -> None:
        apply_selection(self._ui, paciente_id)

    def _open_csv_dialog(self) -> None:
        open_csv_dialog(self)

    def _reset_filters(self) -> None:
        self.filtros.limpiar()

    def _on_historial(self) -> None:
        on_historial(
            parent=self,
            i18n=self._i18n,
            selected_id=obtener_selected_id(self._ui),
            registrar_auditoria=self._uc_auditoria_acceso,
            contexto_usuario=self._container.user_context,
            buscar_citas_uc=self._uc_buscar_historial_citas,
            buscar_recetas_uc=self._uc_buscar_historial_recetas,
            resumen_uc=self._uc_resumen_historial,
            historial_legacy_uc=self._uc_historial,
            detalle_cita_uc=self._uc_detalle_cita,
        )

    def _open_context_menu(self, pos) -> None:
        open_context_menu(
            parent=self,
            table=self.table,
            pos=pos,
            i18n=self._i18n,
            can_write=self._can_write,
            has_selection=obtener_selected_id(self._ui) is not None,
            on_nuevo_cb=self._on_nuevo,
            on_editar_cb=self._on_editar,
            on_desactivar_cb=self._on_desactivar,
            on_historial_cb=self._on_historial,
        )
