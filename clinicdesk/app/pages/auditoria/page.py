from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox, QWidget

from clinicdesk.app.application.usecases.buscar_auditoria_accesos import BuscarAuditoriaAccesos
from clinicdesk.app.application.usecases.exportar_auditoria_csv import (
    ExportacionAuditoriaDemasiadasFilasError,
    ExportacionAuditoriaError,
    ExportarAuditoriaCSV,
)
from clinicdesk.app.application.usecases.filtros_auditoria import PRESET_PERSONALIZADO
from clinicdesk.app.application.usecases.obtener_resumen_auditoria import ObtenerResumenAuditoria
from clinicdesk.app.application.usecases.preflight_integridad_auditoria import IntegridadAuditoriaComprometidaError
from clinicdesk.app.application.usecases.paginacion_incremental import calcular_siguiente_offset
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria
from clinicdesk.app.application.security import UserContext
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.auditoria.acciones_auditoria import limpiar_filtros
from clinicdesk.app.pages.auditoria.contratos_ui import AuditoriaUIRefs
from clinicdesk.app.pages.auditoria.exportador_csv import ExportadorCsvAuditoria
from clinicdesk.app.pages.auditoria.filtros_ui import parse_fecha_iso
from clinicdesk.app.pages.auditoria.preferencias_auditoria import guardar_preferencias, restaurar_preferencias
from clinicdesk.app.pages.auditoria.render_auditoria import apply_selection, render_estado, render_resumen, render_tabla
from clinicdesk.app.pages.auditoria.ui_builder import build_auditoria_ui
from clinicdesk.app.pages.auditoria.workers_auditoria import crear_worker_exportacion
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesosQueries, FiltrosAuditoriaAccesos
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite
from clinicdesk.app.ui.viewmodels.auditoria_viewmodel import AuditoriaViewModel

LOGGER = get_logger(__name__)


class PageAuditoria(QWidget):
    def __init__(self, container: AppContainer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = I18nManager("es")
        self._settings = QSettings("clinicdesk", "ui")
        self._preferencias_service = container.preferencias_service
        self._queries = AuditoriaAccesosQueries(container.connection)
        self._uc_telemetria = RegistrarTelemetria(RepositorioTelemetriaEventosSqlite(container.connection))
        self._contexto_telemetria = UserContext()
        self._uc_buscar = BuscarAuditoriaAccesos(self._queries, verificador_integridad=self._queries)
        self._uc_resumen = ObtenerResumenAuditoria(self._queries)
        self._uc_exportar = ExportarAuditoriaCSV(self._queries, verificador_integridad=self._queries)
        self._exportador = ExportadorCsvAuditoria(self, self._settings, self._tr)
        self._vm = AuditoriaViewModel(self._listar_primer_bloque)
        self._ui: AuditoriaUIRefs = build_auditoria_ui(self, self._tr)
        self._offset_actual, self._limit = 0, 50
        self._total_actual: int | None = None
        self._items_acumulados: list[object] = []
        self._conectar_signals()
        self._vm.subscribe(self._on_estado_vm)
        self._vm.subscribe_eventos(self._on_evento_vm)
        self._retranslate()
        restaurar_preferencias(preferencias_service=self._preferencias_service, ui=self._ui)
        self._cargar_primera_pagina()

    def on_show(self) -> None:
        self._cargar_primera_pagina()

    def _conectar_signals(self) -> None:
        self._ui.combo_rango.currentIndexChanged.connect(self._on_preset_cambiado)
        self._ui.btn_buscar.clicked.connect(self._on_buscar)
        self._ui.btn_limpiar.clicked.connect(self._on_limpiar)
        self._ui.btn_reintentar.clicked.connect(self._on_reintentar)
        self._ui.btn_cargar_mas.clicked.connect(self._on_cargar_mas)
        self._ui.btn_exportar.clicked.connect(self._on_exportar)

    def _retranslate(self) -> None:
        self._ui.btn_buscar.setText(self._tr("auditoria.accion.buscar"))
        self._ui.btn_limpiar.setText(self._tr("auditoria.accion.limpiar"))
        self._ui.btn_cargar_mas.setText(self._tr("auditoria.accion.cargar_mas"))
        self._ui.btn_exportar.setText(self._tr("auditoria.accion.exportar_csv"))
        self._ui.btn_reintentar.setText(self._tr("auditoria.accion.reintentar"))
        self._ui.input_desde.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self._ui.input_hasta.setPlaceholderText(self._tr("auditoria.filtro.fecha_placeholder"))
        self._set_estado("idle")

    def _on_preset_cambiado(self) -> None:
        personalizado = self._ui.combo_rango.currentData() == PRESET_PERSONALIZADO
        self._ui.input_desde.setEnabled(personalizado)
        self._ui.input_hasta.setEnabled(personalizado)

    def _on_buscar(self) -> None:
        guardar_preferencias(preferencias_service=self._preferencias_service, ui=self._ui)
        self._vm.aplicar_filtro(self._ui.input_usuario.text())

    def _on_limpiar(self) -> None:
        limpiar_filtros(self._ui)
        guardar_preferencias(preferencias_service=self._preferencias_service, ui=self._ui)
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
        self._registrar_telemetria("auditoria_cargar_mas", "click")
        self._buscar(incremental=True)

    def _listar_primer_bloque(self, filtro_texto: str) -> list[object]:
        filtros = self._build_filtros(filtro_texto=filtro_texto)
        if filtros is None:
            return []
        result = self._uc_buscar.execute(
            filtros,
            self._limit,
            0,
            preset_rango=self._ui.combo_rango.currentData(),
            total_conocido=None,
        )
        self._items_acumulados = list(result.items)
        self._total_actual = result.total
        self._offset_actual = calcular_siguiente_offset(0, self._limit, result.total)
        self._render_resumen_para(filtros)
        self._set_estado("empty" if result.total == 0 else "ok")
        return list(result.items)

    def _buscar(self, *, incremental: bool) -> None:
        filtros = self._build_filtros(filtro_texto=self._ui.input_usuario.text())
        if filtros is None:
            return
        self._set_estado("loading_more" if incremental else "loading")
        try:
            result = self._uc_buscar.execute(
                filtros,
                self._limit,
                self._offset_actual,
                preset_rango=self._ui.combo_rango.currentData(),
                total_conocido=self._total_actual,
            )
            if not incremental:
                self._render_resumen_para(filtros)
        except Exception:
            self._set_estado("error_more" if incremental and self._items_acumulados else "error")
            LOGGER.warning("auditoria_cargar_mas_fail", extra={"action": "auditoria_cargar_mas_fail"})
            self._registrar_telemetria("auditoria_cargar_mas", "fail")
            return
        self._total_actual = result.total
        self._offset_actual = calcular_siguiente_offset(self._offset_actual, self._limit, result.total)
        if incremental:
            self._items_acumulados.extend(result.items)
            LOGGER.info("auditoria_cargar_mas_ok", extra={"action": "auditoria_cargar_mas_ok"})
            self._registrar_telemetria("auditoria_cargar_mas", "ok")
        else:
            self._items_acumulados = list(result.items)
        self._vm.seleccionar(None)
        self._vm.set_items(list(self._items_acumulados))
        self._set_estado("empty" if result.total == 0 else "ok")

    def _build_filtros(self, *, filtro_texto: str) -> FiltrosAuditoriaAccesos | None:
        desde_texto = self._ui.input_desde.text().strip()
        hasta_texto = self._ui.input_hasta.text().strip()
        desde, hasta = parse_fecha_iso(desde_texto), parse_fecha_iso(hasta_texto)
        if desde_texto and desde is None:
            return self._error_fecha(self._tr("auditoria.filtro.desde"))
        if hasta_texto and hasta is None:
            return self._error_fecha(self._tr("auditoria.filtro.hasta"))
        return FiltrosAuditoriaAccesos(
            usuario_contiene=filtro_texto.strip() or None,
            accion=self._ui.combo_accion.currentData(),
            entidad_tipo=self._ui.combo_entidad.currentData(),
            desde_utc=desde,
            hasta_utc=hasta,
        )

    def _error_fecha(self, campo: str) -> None:
        QMessageBox.warning(
            self, self._tr("auditoria.titulo"), self._tr("auditoria.error.fecha_invalida").format(campo=campo)
        )
        return None

    def _render_resumen_para(self, filtros: FiltrosAuditoriaAccesos) -> None:
        render_resumen(self._ui, self._uc_resumen.execute(filtros.desde_utc, filtros.hasta_utc), self._tr)

    def _on_estado_vm(self, estado) -> None:
        render_tabla(self._ui, list(estado.items), traducir=self._tr)
        apply_selection(self._ui, estado.seleccion_id)

    def _on_evento_vm(self, evento) -> None:
        if evento.tipo != "job":
            return
        if evento.payload.get("accion") == "exportar_auditoria_csv":
            self._run_export_job()

    def _on_exportar(self) -> None:
        if not self._total_actual or not self._exportador.confirmar(self._total_actual):
            return
        self._registrar_telemetria("auditoria_export", "click")
        self._vm.exportar_csv()

    def _run_export_job(self) -> None:
        filtros = self._build_filtros(filtro_texto=self._ui.input_usuario.text())
        if filtros is None:
            return
        ruta_guardado = self._exportador.pedir_ruta_guardado("auditoria_accesos.csv")
        if not ruta_guardado:
            return
        parent_window = self.window()
        if not hasattr(parent_window, "run_premium_job"):
            return

        def _on_success(result: object) -> None:
            if isinstance(result, str):
                self._exportador.registrar_ruta_exito(result)
            self._registrar_telemetria("auditoria_export", "ok")

        try:
            parent_window.run_premium_job(
                job_id="export_auditoria_csv",
                title_key="job.export_auditoria.title",
                worker_factory=lambda: crear_worker_exportacion(
                    ejecutar_exportacion=self._uc_exportar.execute,
                    filtros=filtros,
                    preset_rango=self._ui.combo_rango.currentData(),
                    ruta_guardado=ruta_guardado,
                ),
                cancellable=True,
                toast_success_key="job.done",
                toast_failed_key="job.failed",
                toast_cancelled_key="job.cancelled",
                on_success=_on_success,
            )
        except (
            ExportacionAuditoriaDemasiadasFilasError,
            ExportacionAuditoriaError,
            IntegridadAuditoriaComprometidaError,
        ) as exc:
            self._exportador.mostrar_error(getattr(exc, "reason_code", "unexpected_error"), permitir_reintento=False)
            self._registrar_telemetria("auditoria_export", "fail")
        except OSError as exc:
            self._exportador.mostrar_error("disk_write_error", permitir_reintento=False)
            LOGGER.warning(
                "auditoria_export_fail",
                extra={"action": "auditoria_export_fail", "reason_code": "disk_write_error", "error": str(exc)},
            )
            self._registrar_telemetria("auditoria_export", "fail")

    def _set_estado(self, estado: str) -> None:
        render_estado(
            self._ui,
            estado=estado,
            mostrados=len(self._items_acumulados),
            total=self._total_actual or 0,
            traducir=self._tr,
        )

    def _registrar_telemetria(self, evento: str, resultado: str) -> None:
        try:
            self._uc_telemetria.ejecutar(
                contexto_usuario=self._contexto_telemetria,
                evento=evento,
                contexto=f"page=auditoria;resultado={resultado}",
            )
        except Exception:
            return

    def _tr(self, key: str) -> str:
        return self._i18n.t(key)
