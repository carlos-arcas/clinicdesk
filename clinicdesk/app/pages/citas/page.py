from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QCalendarWidget,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QMessageBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.citas import (
    ATRIBUTOS_CITA,
    BuscarCitasParaCalendario,
    BuscarCitasParaLista,
    FiltrosCitasDTO,
    ErrorValidacionDTO,
    HitoAtencion,
    RegistrarHitoAtencionCita,
    PaginacionCitasDTO,
    formatear_valor_atributo_cita,
    normalizar_y_validar_filtros_citas,
    redactar_texto_busqueda,
    sanear_columnas_citas,
)
from clinicdesk.app.application.citas.navigation_intent import (
    CitasNavigationIntentDTO,
    debe_abrir_detalle,
    es_intent_calidad,
)
from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import RIESGO_NO_DISPONIBLE
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria
from clinicdesk.app.application.prediccion_ausencias.aviso_salud_prediccion import CacheSaludPrediccionPorRefresh
from clinicdesk.app.application.prediccion_operativa.ux_estimaciones import (
    debe_mostrar_aviso_salud_estimacion,
    mensaje_no_disponible_estimacion,
)
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.container import AppContainer
from clinicdesk.app.controllers.citas_controller import CitasController
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.recordatorio_cita_dialog import RecordatorioCitaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_ui import (
    SETTINGS_KEY_ESTIMACIONES_AGENDA,
    SETTINGS_KEY_RIESGO_AGENDA,
    construir_dtos_desde_calendario,
    resolver_texto_riesgo,
)
from clinicdesk.app.pages.citas.widgets.dialogo_selector_columnas_citas import DialogoSelectorColumnasCitas
from clinicdesk.app.pages.citas.intent_helpers import buscar_indice_por_cita_id
from clinicdesk.app.pages.citas.widgets.panel_filtros_citas_widget import PanelFiltrosCitasWidget
from clinicdesk.app.pages.citas.widgets.persistencia_citas_settings import (
    EstadoPersistidoFiltrosCitas,
    clave_columnas_citas,
    claves_filtros_citas,
    deserializar_columnas_citas,
    deserializar_filtros_citas,
    estado_restauracion_columnas,
    serializar_columnas_citas,
    serializar_filtros_citas,
)
from clinicdesk.app.pages.citas.widgets.tooltip_citas import CLAVES_TOOLTIP_POR_DEFECTO, construir_tooltip_cita
from clinicdesk.app.pages.citas.lote_hitos_controller import GestorLoteHitosCitas
from clinicdesk.app.pages.prediccion_operativa.helpers import construir_bullets_explicacion
from clinicdesk.app.queries.citas_queries import CitaRow, CitasQueries
from clinicdesk.app.infrastructure.sqlite.repos_citas_hitos import CitasHitosRepository
from clinicdesk.app.infrastructure.sqlite.db_path import resolver_db_path_desde_conexion

LOGGER = get_logger(__name__)


class _RelojSistema:
    def ahora(self) -> datetime:
        return datetime.now().replace(microsecond=0)


def _payload_log_filtros(filtros: FiltrosCitasDTO, contexto: str) -> dict[str, object]:
    return {
        "action": "citas_filtros_aplicados",
        "contexto": contexto,
        "preset": filtros.rango_preset,
        "desde": filtros.desde.isoformat() if filtros.desde else None,
        "hasta": filtros.hasta.isoformat() if filtros.hasta else None,
        "estado": filtros.estado_cita,
        "medico_id": filtros.medico_id,
        "sala_id": filtros.sala_id,
        "paciente_id": filtros.paciente_id,
        "texto_redactado": redactar_texto_busqueda(filtros.texto_busqueda),
        "filtro_calidad": filtros.filtro_calidad,
    }


class PageCitas(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._queries = CitasQueries(container)
        self._buscar_lista_uc = BuscarCitasParaLista(self._queries)
        self._buscar_calendario_uc = BuscarCitasParaCalendario(self._queries)
        self._controller = CitasController(self, container)
        self._registrar_hito_uc = RegistrarHitoAtencionCita(CitasHitosRepository(container.connection), _RelojSistema())
        self._can_write = container.user_context.can_write
        self._uc_telemetria = RegistrarTelemetria(container.telemetria_eventos_repo)
        self._settings = QSettings("clinicdesk", "ui")
        self._filtros_aplicados = FiltrosCitasDTO()
        self._columnas_lista: tuple[str, ...] = tuple()
        self._citas_lista_ids: list[int] = []
        self._citas_calendario_ids: list[int] = []
        self._intent_navegacion_pendiente: CitasNavigationIntentDTO | None = None
        self._filtros_previos_calidad: FiltrosCitasDTO | None = None
        self._filtro_calidad_activo: str | None = None
        self._citas_seleccionadas: set[int] = set()
        self._actualizando_checks_lote = False
        self._riesgo_enabled = False
        self._estimaciones_enabled = False
        self._token_refresh_salud = 0
        self._token_aviso_logueado: int | None = None
        self._cache_salud_duracion = CacheSaludPrediccionPorRefresh(
            self._container.prediccion_operativa_facade.obtener_salud_duracion
        )
        self._cache_salud_espera = CacheSaludPrediccionPorRefresh(
            self._container.prediccion_operativa_facade.obtener_salud_espera
        )
        self._cache_estimaciones = CacheSaludPrediccionPorRefresh(
            self._container.prediccion_operativa_facade.obtener_estimaciones_agenda
        )
        self._estimaciones_duracion: dict[int, str] = {}
        self._estimaciones_espera: dict[int, str] = {}
        self._db_path = self._resolver_db_path()

        self._build_ui()
        self._bind_events()
        self._restaurar_estado_ui()
        self._refrescar_vistas_principales()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget(self)
        self.calendar = QCalendarWidget()
        self.lbl_date = QLabel(self)
        self.btn_new = QPushButton(self._i18n.t("citas.acciones.nueva"))
        self.btn_delete = QPushButton(self._i18n.t("citas.acciones.eliminar"))
        self.btn_new.setEnabled(self._can_write)
        self.btn_delete.setEnabled(False)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "", "", "", "", "", "", ""])
        self.table.setColumnHidden(0, True)
        self.lbl_aviso_salud_calendario = QLabel(self)
        self.btn_ir_prediccion_calendario = QPushButton(self._i18n.t("estimaciones.ir_a_estimaciones"), self)
        self.btn_ir_prediccion_calendario.clicked.connect(lambda: self._ir_a_estimaciones("calendario"))
        self.lbl_aviso_salud_calendario.setVisible(False)
        self.btn_ir_prediccion_calendario.setVisible(False)

        tab_calendario = QWidget(self)
        izq = QVBoxLayout()
        izq.addWidget(self.calendar)
        izq.addWidget(self.lbl_date)
        izq.addWidget(self.btn_new)
        izq.addWidget(self.btn_delete)
        der = QVBoxLayout()
        aviso_cal = QHBoxLayout()
        aviso_cal.addWidget(self.lbl_aviso_salud_calendario, 1)
        aviso_cal.addWidget(self.btn_ir_prediccion_calendario)
        aviso_cal.addStretch(1)
        der.addLayout(aviso_cal)
        der.addWidget(self.table)
        lay_cal = QHBoxLayout(tab_calendario)
        lay_cal.addLayout(izq, 1)
        lay_cal.addLayout(der, 3)

        tab_lista = QWidget(self)
        self.panel_filtros = PanelFiltrosCitasWidget(self._i18n, tab_lista)
        self.btn_columnas = QPushButton(self._i18n.t("citas.lista.columnas.boton"), tab_lista)
        self.lbl_estado = QLabel("", tab_lista)
        self.btn_reintentar = QPushButton(self._i18n.t("citas.ux.reintentar"), tab_lista)
        self.btn_reintentar.setVisible(False)
        self.lbl_banner_validacion = QLabel("", tab_lista)
        self.btn_corregir_filtros = QPushButton(self._i18n.t("citas.validacion.banner.corregir"), tab_lista)
        self.btn_restablecer_filtros = QPushButton(self._i18n.t("citas.validacion.banner.restablecer"), tab_lista)
        self.lbl_banner_calidad = QLabel("", tab_lista)
        self.btn_quitar_filtro_calidad = QPushButton(self._i18n.t("citas.calidad.quitar_filtro"), tab_lista)
        self.btn_corregir_filtros.setVisible(False)
        self.btn_restablecer_filtros.setVisible(False)
        self.lbl_banner_calidad.setVisible(False)
        self.btn_quitar_filtro_calidad.setVisible(False)
        self.lbl_aviso_columnas = QLabel("", tab_lista)
        self.lbl_aviso_salud_lista = QLabel("", tab_lista)
        self.btn_ir_prediccion_lista = QPushButton(self._i18n.t("estimaciones.ir_a_estimaciones"), tab_lista)
        self.btn_ir_prediccion_lista.clicked.connect(lambda: self._ir_a_estimaciones("lista"))
        self.lbl_aviso_salud_lista.setVisible(False)
        self.btn_ir_prediccion_lista.setVisible(False)
        self.table_lista = QTableWidget(0, 0, tab_lista)
        self.table_lista.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_lista.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chk_seleccionar_todo = QCheckBox(self._i18n.t("citas.hitos.lote.seleccionar_todo"), tab_lista)
        self._lote_hitos = GestorLoteHitosCitas(
            tab_lista,
            self._i18n,
            self._db_path,
            selected_ids=self._ids_seleccionados_lote,
            on_done=self._on_lote_hitos_done,
        )
        self._lote_hitos.retranslate()
        self.chk_seleccionar_todo.setVisible(False)

        barra = QHBoxLayout()
        barra.addWidget(self.btn_columnas)
        barra.addStretch(1)
        barra.addWidget(self.lbl_estado)
        barra.addWidget(self.btn_reintentar)

        layout_lista = QVBoxLayout(tab_lista)
        layout_lista.addWidget(self.panel_filtros)
        banner = QHBoxLayout()
        banner.addWidget(self.lbl_banner_validacion)
        banner.addWidget(self.btn_corregir_filtros)
        banner.addWidget(self.btn_restablecer_filtros)
        banner.addWidget(self.lbl_banner_calidad)
        banner.addWidget(self.btn_quitar_filtro_calidad)
        banner.addStretch(1)
        layout_lista.addLayout(banner)
        layout_lista.addLayout(barra)
        aviso_lista = QHBoxLayout()
        aviso_lista.addWidget(self.lbl_aviso_salud_lista, 1)
        aviso_lista.addWidget(self.btn_ir_prediccion_lista)
        aviso_lista.addStretch(1)
        layout_lista.addLayout(aviso_lista)
        layout_lista.addWidget(self.chk_seleccionar_todo)
        layout_lista.addWidget(self._lote_hitos.barra)
        layout_lista.addWidget(self.lbl_aviso_columnas)
        layout_lista.addWidget(self.table_lista)

        self.tabs.addTab(tab_calendario, self._i18n.t("citas.tabs.calendario"))
        self.tabs.addTab(tab_lista, self._i18n.t("citas.tabs.lista"))
        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

    def _bind_events(self) -> None:
        self.calendar.selectionChanged.connect(self._refresh_calendario)
        self.btn_new.clicked.connect(self._on_new)
        self.btn_delete.clicked.connect(self._on_delete)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_calendario_item_double_clicked)
        self.table.customContextMenuRequested.connect(self._on_calendario_context_menu)
        self.panel_filtros.filtros_aplicados.connect(self._on_filtros_aplicados)
        self.btn_columnas.clicked.connect(self._abrir_selector_columnas)
        self.btn_reintentar.clicked.connect(self._programar_refresco_lista)
        self.btn_corregir_filtros.clicked.connect(self._corregir_filtros)
        self.btn_restablecer_filtros.clicked.connect(self._restablecer_filtros)
        self.btn_quitar_filtro_calidad.clicked.connect(self._quitar_filtro_calidad)
        self.table_lista.itemDoubleClicked.connect(self._on_lista_item_double_clicked)
        self.table_lista.customContextMenuRequested.connect(self._on_lista_context_menu)
        self.table_lista.itemChanged.connect(self._on_lista_item_changed)
        self.chk_seleccionar_todo.stateChanged.connect(self._on_toggle_seleccionar_todo_visible)

    def on_show(self) -> None:
        self._riesgo_enabled = bool(int(self._settings.value(SETTINGS_KEY_RIESGO_AGENDA, 0)))
        self._estimaciones_enabled = bool(int(self._settings.value(SETTINGS_KEY_ESTIMACIONES_AGENDA, 0)))
        self._refrescar_vistas_principales()

    def aplicar_intent(self, intent: CitasNavigationIntentDTO) -> None:
        if es_intent_calidad(intent):
            self._aplicar_intent_calidad(intent)
            return
        self._desactivar_filtro_calidad_temporal()
        self._intent_navegacion_pendiente = intent
        self._filtros_aplicados = FiltrosCitasDTO(
            rango_preset=intent.preset_rango,
            desde=intent.rango_desde or self._filtros_aplicados.desde,
            hasta=intent.rango_hasta or self._filtros_aplicados.hasta,
            texto_busqueda=self._filtros_aplicados.texto_busqueda,
            estado_cita=intent.estado_cita if intent.estado_cita is not None else self._filtros_aplicados.estado_cita,
            medico_id=self._filtros_aplicados.medico_id,
            sala_id=self._filtros_aplicados.sala_id,
            paciente_id=self._filtros_aplicados.paciente_id,
            incluir_riesgo=(
                intent.incluir_riesgo if intent.incluir_riesgo is not None else self._filtros_aplicados.incluir_riesgo
            ),
            recordatorio_filtro=self._filtros_aplicados.recordatorio_filtro,
            limit=self._filtros_aplicados.limit,
            offset=self._filtros_aplicados.offset,
        )
        self.panel_filtros.set_filtros(self._filtros_aplicados)
        if intent.preferir_pestana == "LISTA":
            self.tabs.setCurrentIndex(1)
        elif intent.preferir_pestana == "CALENDARIO":
            self.tabs.setCurrentIndex(0)
        LOGGER.info(
            "citas_intent_aplicado",
            extra={"action": "citas.intent_aplicado", "cita_id": intent.cita_id_destino},
        )
        self._refrescar_vistas_principales()

    def _aplicar_intent_calidad(self, intent: CitasNavigationIntentDTO) -> None:
        self._citas_seleccionadas.clear()
        self._filtros_previos_calidad = self._filtros_aplicados
        self._filtro_calidad_activo = intent.filtro_calidad
        self._intent_navegacion_pendiente = None
        self._filtros_aplicados = FiltrosCitasDTO(
            rango_preset="PERSONALIZADO",
            desde=intent.rango_desde,
            hasta=intent.rango_hasta,
            filtro_calidad=intent.filtro_calidad,
            limit=self._filtros_aplicados.limit,
            offset=self._filtros_aplicados.offset,
        )
        self.panel_filtros.set_filtros(self._filtros_aplicados)
        self.tabs.setCurrentIndex(1)
        self._mostrar_banner_calidad()
        LOGGER.info(
            "citas_filtro_calidad_aplicado",
            extra={"action": "citas_filtro_calidad_aplicado", "filtro_calidad": intent.filtro_calidad},
        )
        self._refrescar_vistas_principales()

    def _mostrar_banner_calidad(self) -> None:
        if not self._filtro_calidad_activo:
            return
        tipo = self._i18n.t(f"citas.calidad.tipo.{self._filtro_calidad_activo.lower()}")
        self.lbl_banner_calidad.setText(self._i18n.t("citas.calidad.banner", tipo=tipo))
        self.lbl_banner_calidad.setVisible(True)
        self.btn_quitar_filtro_calidad.setVisible(True)
        self._actualizar_ui_lote_hitos()

    def _desactivar_filtro_calidad_temporal(self) -> None:
        self._citas_seleccionadas.clear()
        self._filtro_calidad_activo = None
        self._filtros_previos_calidad = None
        self.lbl_banner_calidad.setText("")
        self.lbl_banner_calidad.setVisible(False)
        self.btn_quitar_filtro_calidad.setVisible(False)
        self._actualizar_ui_lote_hitos()

    def _quitar_filtro_calidad(self) -> None:
        self.tabs.setCurrentIndex(1)
        filtros = self._filtros_previos_calidad or FiltrosCitasDTO(rango_preset="SEMANA")
        self._desactivar_filtro_calidad_temporal()
        self._filtros_aplicados = filtros
        self.panel_filtros.set_filtros(self._filtros_aplicados)
        self._refrescar_vistas_principales()

    def _resolver_db_path(self) -> str:
        return resolver_db_path_desde_conexion(self._container.connection)

    def _refrescar_vistas_principales(self) -> None:
        self._token_refresh_salud += 1
        self._token_aviso_logueado = None
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _restaurar_estado_ui(self) -> None:
        filtros = claves_filtros_citas()
        data = EstadoPersistidoFiltrosCitas(
            preset=str(self._settings.value(filtros["preset"], "HOY")),
            desde_iso=self._settings.value(filtros["desde"]),
            hasta_iso=self._settings.value(filtros["hasta"]),
            texto=self._settings.value(filtros["texto"]),
            estado=self._settings.value(filtros["estado"]),
            medico_id=self._settings.value(filtros["medico_id"]),
            sala_id=self._settings.value(filtros["sala_id"]),
            paciente_id=self._settings.value(filtros["paciente_id"]),
        )
        self._filtros_aplicados = deserializar_filtros_citas(data)
        self.panel_filtros.set_filtros(self._filtros_aplicados)
        saved = self._settings.value(clave_columnas_citas())
        columnas = deserializar_columnas_citas(saved)
        self._columnas_lista, restauradas = sanear_columnas_citas(columnas)
        self._actualizar_aviso_columnas(restauradas or estado_restauracion_columnas(saved))

    def _on_filtros_aplicados(self, filtros: object) -> None:
        if not isinstance(filtros, FiltrosCitasDTO):
            return
        resultado = normalizar_y_validar_filtros_citas(filtros, datetime.now(), self._contexto_activo())
        if not resultado.validacion.ok:
            self._mostrar_error_validacion(
                resultado.validacion.errores[0], self._contexto_activo(), resultado.validacion.errores
            )
            return
        self._ocultar_banner_validacion()
        self._filtros_aplicados = resultado.filtros_normalizados
        self._desactivar_filtro_calidad_temporal()
        LOGGER.info(
            "citas_filtros_aplicados", extra=_payload_log_filtros(self._filtros_aplicados, self._contexto_activo())
        )
        self._guardar_filtros()
        self._refrescar_vistas_principales()

    def _guardar_filtros(self) -> None:
        data = serializar_filtros_citas(self._filtros_aplicados)
        for clave, key in claves_filtros_citas().items():
            self._settings.setValue(
                key, getattr(data, f"{clave}_iso", None) if clave in {"desde", "hasta"} else getattr(data, clave)
            )

    def _programar_refresco_lista(self) -> None:
        self._set_estado_lista("citas.ux.cargando", loading=True)
        QTimer.singleShot(0, self._refresh_lista)

    def _refresh_calendario(self) -> None:
        resultado = normalizar_y_validar_filtros_citas(self._filtros_aplicados, datetime.now(), "CALENDARIO")
        if not resultado.validacion.ok:
            self._mostrar_error_validacion(resultado.validacion.errores[0], "CALENDARIO", resultado.validacion.errores)
            self.table.setRowCount(0)
            return
        filtros = resultado.filtros_normalizados
        self.lbl_date.setText(
            self._i18n.t("citas.calendario.fecha").format(fecha=self.calendar.selectedDate().toString("yyyy-MM-dd"))
        )
        try:
            items = self._buscar_calendario_uc.ejecutar(filtros, CLAVES_TOOLTIP_POR_DEFECTO)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning(
                "citas_calendario_error",
                extra={"action": "citas_calendario_error", "error": exc.__class__.__name__, "contexto": "CALENDARIO"},
            )
            self.table.setRowCount(0)
            return
        riesgos = (
            self._obtener_riesgo_citas_calendario([self._mapear_row_calendario(x) for x in items])
            if self._riesgo_enabled
            else {}
        )
        estimaciones = self._obtener_estimaciones_agenda()
        self.table.setRowCount(0)
        self._citas_calendario_ids = []
        for item in items:
            item = dict(item)
            cita_id = int(item["cita_id"])
            item["riesgo_ausencia"] = resolver_texto_riesgo(
                riesgos.get(cita_id, RIESGO_NO_DISPONIBLE), self._i18n
            ).texto
            item["duracion_estimada"] = self._texto_estimacion(
                estimaciones[0].get(cita_id, "NO_DISPONIBLE"), "duracion", True
            )
            item["espera_estimada"] = self._texto_estimacion(
                estimaciones[1].get(cita_id, "NO_DISPONIBLE"), "espera", True
            )
            self._agregar_fila_calendario(item)
            self._citas_calendario_ids.append(cita_id)
        self._actualizar_aviso_salud_prediccion("calendario")
        self._resolver_intent_navegacion("CALENDARIO")

    def _refresh_lista(self) -> None:
        if self._filtro_calidad_activo:
            self._citas_seleccionadas.clear()
        validacion = normalizar_y_validar_filtros_citas(self._filtros_aplicados, datetime.now(), "LISTA")
        if not validacion.validacion.ok:
            self._mostrar_error_validacion(validacion.validacion.errores[0], "LISTA", validacion.validacion.errores)
            self._render_lista([])
            self._set_estado_lista(None)
            return
        try:
            resultado = self._buscar_lista_uc.ejecutar(
                validacion.filtros_normalizados, self._columnas_lista, PaginacionCitasDTO(limit=500, offset=0)
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning(
                "citas_lista_error",
                extra={"action": "citas_lista_error", "error": exc.__class__.__name__, "contexto": "LISTA"},
            )
            self._set_estado_lista("citas.ux.error", error=True)
            return
        self._ocultar_banner_validacion()
        self._render_lista(self._inyectar_estimaciones(resultado.items))
        self._actualizar_aviso_salud_prediccion("lista")
        if not resultado.items:
            self._set_estado_lista("citas.ux.vacio")
        else:
            self._set_estado_lista(None)
        self._resolver_intent_navegacion("LISTA")

    def _render_lista(self, rows: list[dict[str, object]]) -> None:
        self._actualizando_checks_lote = True
        self.table_lista.setRowCount(0)
        columnas, _ = sanear_columnas_citas(self._columnas_lista)
        visibles = [c for c in columnas if c != "cita_id"]
        mostrar_lote = bool(self._filtro_calidad_activo)
        headers_visibles = [self._i18n.t("citas.hitos.lote.columna_seleccion")] if mostrar_lote else []
        headers = {x.clave: self._i18n.t(x.i18n_key_cabecera) for x in ATRIBUTOS_CITA}
        headers_visibles.extend(headers[c] for c in visibles)
        self.table_lista.setColumnCount(len(headers_visibles))
        self.table_lista.setHorizontalHeaderLabels(headers_visibles)
        self._citas_lista_ids = [int(row["cita_id"]) for row in rows]
        for row in rows:
            idx = self.table_lista.rowCount()
            self.table_lista.insertRow(idx)
            offset = 0
            cita_id = int(row["cita_id"])
            if mostrar_lote:
                check_item = QTableWidgetItem()
                check_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                check_item.setCheckState(Qt.Checked if cita_id in self._citas_seleccionadas else Qt.Unchecked)
                self.table_lista.setItem(idx, 0, check_item)
                offset = 1
            for col, clave in enumerate(visibles):
                self.table_lista.setItem(idx, col + offset, QTableWidgetItem(formatear_valor_atributo_cita(clave, row)))
        self._actualizando_checks_lote = False
        self._actualizar_ui_lote_hitos()

    def _resolver_intent_navegacion(self, vista: str) -> None:
        intent = self._intent_navegacion_pendiente
        if intent is None or vista != self._contexto_activo():
            return
        encontrado, vista_final = self._resolver_seleccion_intent(intent, vista)
        if encontrado and intent.resaltar:
            self._aplicar_resaltado_intent(intent, vista_final)
        self._abrir_detalle_segun_intent(intent, encontrado, vista_final)
        if not encontrado:
            self.lbl_estado.setText(self._i18n.t("gestion.abrir_no_encontrada"))
        LOGGER.info(
            "citas_intent_aplicado",
            extra={
                "action": "citas_intent_aplicado",
                "accion": intent.accion,
                "cita_id": intent.cita_id_destino,
                "found": encontrado,
                "vista_final": vista_final,
            },
        )
        try:
            self._uc_telemetria.ejecutar(
                contexto_usuario=self._container.user_context,
                evento="citas_intent_aplicado",
                contexto=f"vista={vista_final};found={int(encontrado)}",
                entidad_tipo="cita",
                entidad_id=intent.cita_id_destino,
            )
        except Exception:
            pass
        self._intent_navegacion_pendiente = None

    def _resolver_seleccion_intent(self, intent: CitasNavigationIntentDTO, vista: str) -> tuple[bool, str]:
        if self._seleccionar_cita_intent(intent, vista):
            return True, vista
        if vista != "CALENDARIO":
            return False, vista
        self.tabs.setCurrentIndex(1)
        if self._seleccionar_cita_intent(intent, "LISTA"):
            return True, "LISTA"
        return False, "LISTA"

    def _abrir_detalle_segun_intent(self, intent: CitasNavigationIntentDTO, found: bool, vista_final: str) -> None:
        if not debe_abrir_detalle(intent, found):
            return
        ok = self._abrir_detalle_cita_por_id(intent.cita_id_destino, vista_final)
        action = "citas_abrir_detalle_ok" if ok else "citas_abrir_detalle_fail"
        payload = {"action": action, "cita_id": intent.cita_id_destino, "vista": vista_final}
        if ok:
            LOGGER.info(action, extra=payload)
            return
        self.lbl_estado.setText(self._i18n.t("gestion.abrir_detalle_no_posible"))
        LOGGER.warning(action, extra={**payload, "exc_type": "DetalleNoDisponible"})

    def _aplicar_resaltado_intent(self, intent: CitasNavigationIntentDTO, vista: str) -> None:
        indice = self._indice_intent_en_vista(intent.cita_id_destino, vista)
        if indice is None:
            return
        tabla = self.table_lista if vista == "LISTA" else self.table
        self._resaltar_fila_temporal(tabla, indice, intent.duracion_resaltado_ms)

    def _indice_intent_en_vista(self, cita_id: int, vista: str) -> int | None:
        if vista == "LISTA":
            return buscar_indice_por_cita_id(self._citas_lista_ids, cita_id)
        return buscar_indice_por_cita_id(self._citas_calendario_ids, cita_id)

    def _resaltar_fila_temporal(self, tabla: QTableWidget, fila: int, duracion_ms: int) -> None:
        if fila < 0 or fila >= tabla.rowCount():
            return
        color = QColor("#FFF2B2")
        originales: list[QColor | None] = []
        for col in range(tabla.columnCount()):
            item = tabla.item(fila, col)
            if item is None:
                originales.append(None)
                continue
            originales.append(item.background().color())
            item.setBackground(color)

        def restaurar() -> None:
            if fila >= tabla.rowCount():
                return
            for col, fondo in enumerate(originales):
                item = tabla.item(fila, col)
                if item is None or fondo is None:
                    continue
                item.setBackground(fondo)

        QTimer.singleShot(max(0, duracion_ms), restaurar)

    def _abrir_detalle_cita_por_id(self, cita_id: int, vista: str) -> bool:
        if vista == "LISTA":
            indice = buscar_indice_por_cita_id(self._citas_lista_ids, cita_id)
            if indice is None:
                return False
            item = self.table_lista.item(indice, 0)
            if item is None:
                return False
            self._on_lista_item_double_clicked(item)
            return self._riesgo_enabled
        indice = buscar_indice_por_cita_id(self._citas_calendario_ids, cita_id)
        if indice is None:
            return False
        item = self.table.item(indice, 0)
        if item is None:
            return False
        self._on_calendario_item_double_clicked(item)
        return self._riesgo_enabled

    def _seleccionar_cita_intent(self, intent: CitasNavigationIntentDTO, vista: str) -> bool:
        indice = self._indice_intent_en_vista(intent.cita_id_destino, vista)
        if indice is None:
            return False
        if vista == "LISTA":
            self.table_lista.selectRow(indice)
            item = self.table_lista.item(indice, 0)
            if item is not None:
                self.table_lista.scrollToItem(item)
            return True
        self.table.selectRow(indice)
        item = self.table.item(indice, 0)
        if item is not None:
            self.table.scrollToItem(item)
        return True

    def _agregar_fila_calendario(self, item: dict[str, object]) -> None:
        idx = self.table.rowCount()
        self.table.insertRow(idx)
        valores = [
            str(item.get("cita_id", "")),
            formatear_valor_atributo_cita("fecha", item),
            formatear_valor_atributo_cita("hora_inicio", item),
            formatear_valor_atributo_cita("paciente", item),
            formatear_valor_atributo_cita("medico", item),
            formatear_valor_atributo_cita("sala", item),
            formatear_valor_atributo_cita("estado", item),
            formatear_valor_atributo_cita("incidencias", item),
        ]
        tooltip = construir_tooltip_cita(self._i18n, item)
        for col, valor in enumerate(valores):
            celda = QTableWidgetItem(valor)
            celda.setToolTip(tooltip)
            self.table.setItem(idx, col, celda)

    def _set_estado_lista(self, i18n_key: str | None, loading: bool = False, error: bool = False) -> None:
        self.lbl_estado.setText(self._i18n.t(i18n_key) if i18n_key else "")
        self.btn_reintentar.setVisible(error)
        self.btn_columnas.setEnabled(not loading)
        self.panel_filtros.setEnabled(not loading)

    def _abrir_selector_columnas(self) -> None:
        dialogo = DialogoSelectorColumnasCitas(self._i18n, self._columnas_lista, self)
        if dialogo.exec() != dialogo.Accepted:
            return
        self._columnas_lista = dialogo.columnas_seleccionadas()
        self._settings.setValue(clave_columnas_citas(), serializar_columnas_citas(self._columnas_lista))
        self._actualizar_aviso_columnas(False)
        self._programar_refresco_lista()

    def _contexto_activo(self) -> str:
        return "LISTA" if self.tabs.currentIndex() == 1 else "CALENDARIO"

    def _mostrar_error_validacion(
        self, primer_error: ErrorValidacionDTO, contexto: str, errores: tuple[ErrorValidacionDTO, ...]
    ) -> None:
        self.lbl_banner_validacion.setText(
            self._i18n.t("citas.validacion.banner.titulo").format(error=self._i18n.t(primer_error.i18n_key))
        )
        self.btn_corregir_filtros.setVisible(True)
        self.btn_restablecer_filtros.setVisible(True)
        self.btn_corregir_filtros.setProperty("campo_error", primer_error.campo)
        LOGGER.info(
            "citas_validacion_fail",
            extra={"action": "citas_validacion_fail", "codes": [item.code for item in errores], "contexto": contexto},
        )

    def _ocultar_banner_validacion(self) -> None:
        self.lbl_banner_validacion.setText("")
        self.btn_corregir_filtros.setVisible(False)
        self.btn_restablecer_filtros.setVisible(False)

    def _corregir_filtros(self) -> None:
        self.tabs.setCurrentIndex(1)
        campo = self.btn_corregir_filtros.property("campo_error")
        self.panel_filtros.enfocar_campo(str(campo) if campo else None)

    def _restablecer_filtros(self) -> None:
        self.tabs.setCurrentIndex(1)
        self._desactivar_filtro_calidad_temporal()
        self.panel_filtros.restablecer_semana()
        self._on_filtros_aplicados(self.panel_filtros.construir_dto())

    def _actualizar_aviso_columnas(self, restauradas: bool) -> None:
        self.lbl_aviso_columnas.setText(self._i18n.t("citas.lista.columnas.restauradas") if restauradas else "")

    def _mapear_row_calendario(self, fila: dict[str, object]) -> CitaRow:
        return CitaRow(
            id=int(fila.get("cita_id", 0)),
            inicio=str(fila.get("inicio", "")),
            fin=str(fila.get("fin", "")),
            paciente_id=int(fila.get("paciente_id", 0)),
            paciente_nombre=str(fila.get("paciente", "")),
            medico_id=int(fila.get("medico_id", 0)),
            medico_nombre=str(fila.get("medico", "")),
            sala_id=int(fila.get("sala_id", 0)),
            sala_nombre=str(fila.get("sala", "")),
            estado=str(fila.get("estado", "")),
            motivo=None,
        )

    def _obtener_riesgo_citas_calendario(self, rows: list[CitaRow]) -> dict[int, str]:
        return self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc.ejecutar(
            construir_dtos_desde_calendario(rows, datetime.now())
        )

    def _obtener_estimaciones_agenda(self) -> tuple[dict[int, str], dict[int, str]]:
        if not self._estimaciones_enabled:
            self._estimaciones_duracion = {}
            self._estimaciones_espera = {}
            return {}, {}
        duraciones, esperas = self._cache_estimaciones.obtener(self._token_refresh_salud)
        self._estimaciones_duracion = duraciones
        self._estimaciones_espera = esperas
        return duraciones, esperas

    def _texto_estimacion(self, nivel: str, tipo: str, mostrar_cta: bool = False) -> str:
        if nivel in {"BAJO", "MEDIO", "ALTO"}:
            return self._i18n.t(f"citas.prediccion_operativa.valor.{nivel.lower()}")
        base = self._i18n.t(mensaje_no_disponible_estimacion(tipo)).format(
            tipo=self._i18n.t(f"estimaciones.tipo.{tipo}")
        )
        if not mostrar_cta:
            return base
        return f"{base} ({self._i18n.t('estimaciones.ir_a_estimaciones')})"

    def _inyectar_estimaciones(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        duraciones, esperas = self._obtener_estimaciones_agenda()
        if not self._estimaciones_enabled:
            return rows
        enriched: list[dict[str, object]] = []
        for row in rows:
            cita_id = int(row.get("cita_id", 0))
            item = dict(row)
            item["duracion_estimada"] = self._texto_estimacion(
                duraciones.get(cita_id, "NO_DISPONIBLE"), "duracion", True
            )
            item["espera_estimada"] = self._texto_estimacion(esperas.get(cita_id, "NO_DISPONIBLE"), "espera", True)
            enriched.append(item)
        return enriched

    def _on_lista_item_double_clicked(self, item: QTableWidgetItem) -> None:
        cita_id = self._cita_id_lista(item.row())
        if cita_id and self._riesgo_enabled:
            self._abrir_dialogo_riesgo(cita_id)

    def _on_calendario_item_double_clicked(self, item: QTableWidgetItem) -> None:
        if self._riesgo_enabled and (cita_id := self._cita_id_calendario(item.row())):
            self._abrir_dialogo_riesgo(cita_id)

    def _on_lista_context_menu(self, point) -> None:
        item = self.table_lista.itemAt(point)
        if item is None:
            return
        self._abrir_menu_cita(self._cita_id_lista(item.row()), self.table_lista.mapToGlobal(point), "lista")

    def _on_lista_item_changed(self, item: QTableWidgetItem) -> None:
        if self._actualizando_checks_lote or not self._filtro_calidad_activo or item.column() != 0:
            return
        cita_id = self._cita_id_lista(item.row())
        if cita_id is None:
            return
        if item.checkState() == Qt.Checked:
            self._citas_seleccionadas.add(cita_id)
        else:
            self._citas_seleccionadas.discard(cita_id)
        self._actualizar_ui_lote_hitos()

    def _on_toggle_seleccionar_todo_visible(self, estado: int) -> None:
        if self._actualizando_checks_lote or not self._filtro_calidad_activo:
            return
        self._actualizando_checks_lote = True
        seleccionado = estado == Qt.Checked
        for row in range(self.table_lista.rowCount()):
            cita_id = self._cita_id_lista(row)
            if cita_id is None:
                continue
            item = self.table_lista.item(row, 0)
            if item is None:
                continue
            item.setCheckState(Qt.Checked if seleccionado else Qt.Unchecked)
            if seleccionado:
                self._citas_seleccionadas.add(cita_id)
            else:
                self._citas_seleccionadas.discard(cita_id)
        self._actualizando_checks_lote = False
        self._actualizar_ui_lote_hitos()

    def _actualizar_ui_lote_hitos(self) -> None:
        filtro_activo = bool(self._filtro_calidad_activo)
        self.chk_seleccionar_todo.setVisible(filtro_activo and bool(self._citas_lista_ids))
        self._actualizar_check_seleccionar_todo_visible(filtro_activo)
        self._lote_hitos.actualizar_visibilidad(len(self._citas_seleccionadas), filtro_activo)

    def _actualizar_check_seleccionar_todo_visible(self, filtro_activo: bool) -> None:
        self.chk_seleccionar_todo.blockSignals(True)
        if not filtro_activo or not self._citas_lista_ids:
            self.chk_seleccionar_todo.setCheckState(Qt.Unchecked)
        else:
            total = len(self._citas_lista_ids)
            seleccionadas = len([cita for cita in self._citas_lista_ids if cita in self._citas_seleccionadas])
            if seleccionadas == 0:
                self.chk_seleccionar_todo.setCheckState(Qt.Unchecked)
            elif seleccionadas == total:
                self.chk_seleccionar_todo.setCheckState(Qt.Checked)
            else:
                self.chk_seleccionar_todo.setCheckState(Qt.PartiallyChecked)
        self.chk_seleccionar_todo.blockSignals(False)

    def _ids_seleccionados_lote(self) -> tuple[int, ...]:
        return tuple(sorted(self._citas_seleccionadas))

    def _on_lote_hitos_done(self) -> None:
        self._refresh_lista()

    def _on_calendario_context_menu(self, point) -> None:
        item = self.table.itemAt(point)
        if item is None:
            return
        self._abrir_menu_cita(self._cita_id_calendario(item.row()), self.table.mapToGlobal(point), "calendario")

    def _abrir_menu_cita(self, cita_id: int | None, global_point, vista: str) -> None:
        if cita_id is None:
            return
        menu = QMenu(self)
        action_recordatorio = QAction(self._i18n.t("recordatorio.accion.preparar"), self)
        action_recordatorio.triggered.connect(lambda: self._abrir_dialogo_recordatorio(cita_id))
        menu.addAction(action_recordatorio)
        menu.addSeparator()
        self._agregar_accion_hito(menu, cita_id, "citas.hitos.marcar_llegada", HitoAtencion.CHECK_IN)
        self._agregar_accion_hito(menu, cita_id, "citas.hitos.llamar_consulta", HitoAtencion.LLAMADO)
        self._agregar_accion_hito(menu, cita_id, "citas.hitos.iniciar_consulta", HitoAtencion.INICIO_CONSULTA)
        self._agregar_accion_hito(menu, cita_id, "citas.hitos.finalizar_consulta", HitoAtencion.FIN_CONSULTA)
        self._agregar_accion_hito(menu, cita_id, "citas.hitos.marcar_salida", HitoAtencion.CHECK_OUT)
        self._agregar_acciones_ver_por_que(menu, cita_id, vista)
        menu.exec(global_point)

    def _agregar_acciones_ver_por_que(self, menu: QMenu, cita_id: int, vista: str) -> None:
        if not self._estimaciones_enabled:
            return
        disponibles = self._tipos_estimacion_disponibles(cita_id)
        if vista == "lista":
            if disponibles:
                self._agregar_accion_ver_por_que(menu, cita_id, disponibles[0], False)
            return
        for tipo in disponibles:
            self._agregar_accion_ver_por_que(menu, cita_id, tipo, True)

    def _tipos_estimacion_disponibles(self, cita_id: int) -> list[str]:
        disponibles: list[str] = []
        if self._estimaciones_duracion.get(cita_id, "NO_DISPONIBLE") != "NO_DISPONIBLE":
            disponibles.append("duracion")
        if self._estimaciones_espera.get(cita_id, "NO_DISPONIBLE") != "NO_DISPONIBLE":
            disponibles.append("espera")
        return disponibles

    def _agregar_accion_ver_por_que(self, menu: QMenu, cita_id: int, tipo: str, incluir_tipo: bool) -> None:
        etiqueta = self._i18n.t("estimaciones.ver_por_que")
        if incluir_tipo:
            etiqueta = f"{etiqueta} ({self._i18n.t(f'estimaciones.tipo.{tipo}')})"
        accion = QAction(etiqueta, self)
        accion.triggered.connect(lambda: self._mostrar_explicacion_estimacion(cita_id, tipo))
        menu.addAction(accion)

    def _mostrar_explicacion_estimacion(self, cita_id: int, tipo: str) -> None:
        nivel = (
            self._estimaciones_duracion.get(cita_id, "NO_DISPONIBLE")
            if tipo == "duracion"
            else self._estimaciones_espera.get(cita_id, "NO_DISPONIBLE")
        )
        if nivel == "NO_DISPONIBLE":
            return
        LOGGER.info(
            "estimaciones_ver_por_que_click",
            extra={"action": "estimaciones_ver_por_que_click", "tipo": tipo},
        )
        if tipo == "duracion":
            explicacion = self._container.prediccion_operativa_facade.obtener_explicacion_duracion(cita_id, nivel)
        else:
            explicacion = self._container.prediccion_operativa_facade.obtener_explicacion_espera(cita_id, nivel)
        titulo = f"{self._i18n.t('estimaciones.ver_por_que')} ({self._i18n.t(f'estimaciones.tipo.{tipo}')})"
        QMessageBox.information(self, titulo, construir_bullets_explicacion(explicacion, self._i18n))

    def _agregar_accion_hito(self, menu: QMenu, cita_id: int, i18n_key: str, hito: HitoAtencion) -> None:
        accion = QAction(self._i18n.t(i18n_key), self)
        accion.triggered.connect(lambda: self._registrar_hito_desde_ui(cita_id, hito))
        menu.addAction(accion)

    def _registrar_hito_desde_ui(self, cita_id: int, hito: HitoAtencion) -> None:
        resultado = self._registrar_hito_uc.ejecutar(cita_id, hito)
        self.lbl_estado.setText(self._i18n.t(f"citas.hitos.resultado.{resultado.reason_code}"))
        self._refrescar_vistas_principales()

    def _cita_id_lista(self, row: int) -> int | None:
        return self._citas_lista_ids[row] if 0 <= row < len(self._citas_lista_ids) else None

    def _cita_id_calendario(self, row: int) -> int | None:
        item = self.table.item(row, 0)
        return int(item.text()) if item and item.text().isdigit() else None

    def _selected_id(self) -> Optional[int]:
        return self._cita_id_calendario(self.table.currentRow())

    def _on_selection_changed(self) -> None:
        self.btn_delete.setEnabled(self._can_write and self._selected_id() is not None)

    def _on_new(self) -> None:
        if self._can_write and self._controller.create_cita_flow(self.calendar.selectedDate().toString("yyyy-MM-dd")):
            self._refrescar_vistas_principales()

    def _on_delete(self) -> None:
        cita_id = self._selected_id()
        if self._can_write and cita_id and self._controller.delete_cita(cita_id):
            self._refrescar_vistas_principales()

    def _actualizar_aviso_salud_prediccion(self, page: str) -> None:
        salud_duracion = self._cache_salud_duracion.obtener(self._token_refresh_salud).estado
        salud_espera = self._cache_salud_espera.obtener(self._token_refresh_salud).estado
        mostrar = debe_mostrar_aviso_salud_estimacion(
            self._estimaciones_enabled, salud_duracion
        ) or debe_mostrar_aviso_salud_estimacion(self._estimaciones_enabled, salud_espera)
        texto = self._i18n.t("estimaciones.aviso_salud") if mostrar else ""
        self.lbl_aviso_salud_calendario.setText(texto)
        self.lbl_aviso_salud_lista.setText(texto)
        self.lbl_aviso_salud_calendario.setVisible(mostrar)
        self.lbl_aviso_salud_lista.setVisible(mostrar)
        self.btn_ir_prediccion_calendario.setVisible(mostrar)
        self.btn_ir_prediccion_lista.setVisible(mostrar)
        if mostrar and self._token_aviso_logueado != self._token_refresh_salud:
            LOGGER.info(
                "estimaciones_aviso_salud_mostrar",
                extra={
                    "action": "estimaciones_aviso_salud_mostrar",
                    "page": page,
                    "duracion": salud_duracion,
                    "espera": salud_espera,
                },
            )
            self._token_aviso_logueado = self._token_refresh_salud

    def _ir_a_estimaciones(self, view: str) -> None:
        LOGGER.info(
            "estimaciones_cta_ir_click",
            extra={"action": "estimaciones_cta_ir_click", "page": "citas", "view": view},
        )
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate("prediccion_operativa")

    def _abrir_dialogo_recordatorio(self, cita_id: int) -> None:
        RecordatorioCitaDialog(self._container, self._i18n, cita_id, self).exec()

    def _abrir_dialogo_riesgo(self, cita_id: int) -> None:
        explicacion = self._container.prediccion_ausencias_facade.obtener_explicacion_riesgo_uc.ejecutar(cita_id)
        salud = self._container.prediccion_ausencias_facade.obtener_salud_uc.ejecutar()
        dialog = RiesgoAusenciaDialog(self._i18n, explicacion, salud, self)
        dialog.exec()
