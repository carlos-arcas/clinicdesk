from __future__ import annotations
from datetime import date
from pathlib import Path
from PySide6.QtCore import QSettings, QThread, QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)
from clinicdesk.app.application.prediccion_ausencias import ResultadoEntrenamientoPrediccion
from clinicdesk.app.application.prediccion_ausencias.resultados_recientes import DiagnosticoResultadosRecientes
from clinicdesk.app.application.prediccion_ausencias.preferencias_recordatorio_entrenar import (
    DIAS_SNOOZE_POR_DEFECTO,
    PreferenciaRecordatorioEntrenarDTO,
    debe_mostrar_recordatorio,
)
from clinicdesk.app.application.prediccion_ausencias.preferencias_resultados_recientes import (
    CLAVE_VENTANA_RESULTADOS_RECIENTES,
    VENTANA_RESULTADOS_POR_DEFECTO,
    deserializar_ventana_resultados_semanas,
    serializar_ventana_resultados_semanas,
)
from clinicdesk.app.application.services.prediccion_ausencias_facade import PrediccionAusenciasFacade
from clinicdesk.app.bootstrap_logging import get_contexto_log, get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.infrastructure.prediccion_ausencias.incidentes import escribir_incidente_entrenamiento
from clinicdesk.app.pages.prediccion_ausencias.cerrar_citas_antiguas_dialog import CerrarCitasAntiguasDialog
from clinicdesk.app.pages.prediccion_ausencias.entrenar_worker import (
    EntrenamientoFailPayload,
    EntrenarPrediccionWorker,
)
from clinicdesk.app.pages.prediccion_ausencias.error_handling import normalizar_error_entrenamiento
from clinicdesk.app.pages.prediccion_ausencias.persistencia_recordatorio_entrenar_settings import (
    leer_preferencia_recordatorio_entrenar,
    limpiar_recordatorio_entrenar,
    posponer_recordatorio_entrenar,
)
LOGGER = get_logger(__name__)
class PagePrediccionAusencias(QWidget):
    def __init__(self, facade: PrediccionAusenciasFacade, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
        self._i18n = i18n
        self._datos_aptos = False
        self._entrenamiento_activo = False
        self._entrenar_thread: QThread | None = None
        self._entrenar_worker: EntrenarPrediccionWorker | None = None
        self._settings_key = "prediccion_ausencias/mostrar_riesgo_agenda"
        self._settings_estimaciones_key = "prediccion_operativa/mostrar_estimaciones_agenda"
        self._ventana_resultados_semanas = VENTANA_RESULTADOS_POR_DEFECTO
        self._recordatorio_oculto_sesion = False
        self._ultimo_motivo_recordatorio_log: str | None = None
        self._preferencia_recordatorio = PreferenciaRecordatorioEntrenarDTO(
            fecha_recordatorio_utc=None,
            dias_snooze=DIAS_SNOOZE_POR_DEFECTO,
        )
        self._build_ui()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()
        self._restaurar_preferencia()
    def on_show(self) -> None:
        self._comprobar_datos()
        self._cargar_previsualizacion()
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(self._build_salud())
        root.addWidget(self._build_resultados_recientes())
        root.addWidget(self._build_paso_1())
        root.addWidget(self._build_paso_2())
        root.addWidget(self._build_paso_3())
        root.addWidget(self._build_activacion())
    def _build_salud(self) -> QWidget:
        self.box_salud = QGroupBox()
        layout = QVBoxLayout(self.box_salud)
        self.lbl_salud_estado = QLabel()
        self.lbl_salud_mensaje = QLabel()
        self.lbl_salud_mensaje.setWordWrap(True)
        self.btn_salud_entrenar = QPushButton()
        self.btn_salud_entrenar.clicked.connect(self._on_entrenar_click)
        self.lbl_salud_ayuda_cierre = QLabel()
        self.lbl_salud_ayuda_cierre.setWordWrap(True)
        self.btn_cerrar_citas_antiguas = QPushButton()
        self.btn_cerrar_citas_antiguas.clicked.connect(self._abrir_asistente_cierre)
        self.banner_recordatorio = QWidget()
        fila_recordatorio = QHBoxLayout(self.banner_recordatorio)
        fila_recordatorio.setContentsMargins(8, 4, 8, 4)
        self.lbl_recordatorio = QLabel()
        self.lbl_recordatorio.setWordWrap(True)
        self.btn_recordatorio_entrenar = QPushButton()
        self.btn_recordatorio_entrenar.clicked.connect(self._on_entrenar_click)
        self.btn_recordatorio_mas_tarde = QPushButton()
        self.btn_recordatorio_mas_tarde.clicked.connect(self._on_recordatorio_mas_tarde)
        fila_recordatorio.addWidget(self.lbl_recordatorio, 1)
        fila_recordatorio.addWidget(self.btn_recordatorio_entrenar)
        fila_recordatorio.addWidget(self.btn_recordatorio_mas_tarde)
        self.banner_recordatorio.setVisible(False)
        layout.addWidget(self.lbl_salud_estado)
        layout.addWidget(self.lbl_salud_mensaje)
        layout.addWidget(self.btn_salud_entrenar)
        layout.addWidget(self.banner_recordatorio)
        layout.addWidget(self.btn_cerrar_citas_antiguas)
        layout.addWidget(self.lbl_salud_ayuda_cierre)
        return self.box_salud
    def _build_resultados_recientes(self) -> QWidget:
        self.box_resultados = QGroupBox()
        layout = QVBoxLayout(self.box_resultados)
        top_row = QHBoxLayout()
        self.lbl_resultados_periodo = QLabel()
        self.cmb_resultados_periodo = QComboBox()
        self.cmb_resultados_periodo.currentIndexChanged.connect(self._on_cambio_periodo_resultados)
        self.btn_resultados_ayuda = QPushButton()
        self.btn_resultados_ayuda.setFlat(True)
        self.btn_resultados_ayuda.clicked.connect(self._mostrar_ayuda_resultados)
        top_row.addWidget(self.lbl_resultados_periodo)
        top_row.addWidget(self.cmb_resultados_periodo)
        top_row.addStretch(1)
        top_row.addWidget(self.btn_resultados_ayuda)
        self.lbl_resultados_subtitulo = QLabel()
        self.lbl_resultados_subtitulo.setWordWrap(True)
        self.lbl_resultados_estado = QLabel()
        self.lbl_resultados_estado.setWordWrap(True)
        self.lbl_resultados_accion = QLabel()
        self.lbl_resultados_accion.setWordWrap(True)
        self.btn_resultados_cerrar_citas_antiguas = QPushButton()
        self.btn_resultados_cerrar_citas_antiguas.clicked.connect(self._on_cta_cerrar_citas_antiguas)
        self.btn_resultados_abrir_confirmaciones = QPushButton()
        self.btn_resultados_abrir_confirmaciones.clicked.connect(self._on_cta_abrir_confirmaciones)
        self.btn_resultados_activar_riesgo_agenda = QPushButton()
        self.btn_resultados_activar_riesgo_agenda.clicked.connect(self._on_cta_activar_riesgo_agenda)
        self.lbl_resultado_bajo = QLabel()
        self.lbl_resultado_medio = QLabel()
        self.lbl_resultado_alto = QLabel()
        layout.addLayout(top_row)
        layout.addWidget(self.lbl_resultados_subtitulo)
        layout.addWidget(self.lbl_resultados_estado)
        layout.addWidget(self.lbl_resultados_accion)
        layout.addWidget(self.btn_resultados_cerrar_citas_antiguas)
        layout.addWidget(self.btn_resultados_abrir_confirmaciones)
        layout.addWidget(self.btn_resultados_activar_riesgo_agenda)
        layout.addWidget(self.lbl_resultado_bajo)
        layout.addWidget(self.lbl_resultado_medio)
        layout.addWidget(self.lbl_resultado_alto)
        return self.box_resultados
    def _build_paso_1(self) -> QWidget:
        self.box_paso_1 = QGroupBox()
        form = QFormLayout(self.box_paso_1)
        self.lbl_paso_1_estado = QLabel()
        self.lbl_paso_1_mensaje = QLabel()
        self.lbl_paso_1_mensaje.setWordWrap(True)
        form.addRow(self.lbl_paso_1_estado)
        form.addRow(self.lbl_paso_1_mensaje)
        return self.box_paso_1
    def _build_paso_2(self) -> QWidget:
        self.box_paso_2 = QGroupBox()
        layout = QVBoxLayout(self.box_paso_2)
        self.btn_entrenar = QPushButton()
        self.btn_entrenar.clicked.connect(self._on_entrenar_click)
        self.lbl_paso_2_estado = QLabel()
        self.lbl_paso_2_estado.setWordWrap(True)
        self.progress_entrenamiento = QProgressBar()
        self.progress_entrenamiento.setRange(0, 0)
        self.progress_entrenamiento.setVisible(False)
        self.btn_reintentar = QPushButton()
        self.btn_reintentar.clicked.connect(self._on_entrenar_click)
        self.btn_reintentar.setVisible(False)
        layout.addWidget(self.btn_entrenar)
        layout.addWidget(self.lbl_paso_2_estado)
        layout.addWidget(self.progress_entrenamiento)
        layout.addWidget(self.btn_reintentar)
        return self.box_paso_2
    def _build_paso_3(self) -> QWidget:
        self.box_paso_3 = QGroupBox()
        layout = QVBoxLayout(self.box_paso_3)
        self.lbl_paso_3_estado = QLabel()
        self.lbl_paso_3_estado.setWordWrap(True)
        self.tabla = QTableWidget(0, 5)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.lbl_paso_3_estado)
        layout.addWidget(self.tabla)
        return self.box_paso_3
    def _build_activacion(self) -> QWidget:
        panel = QWidget()
        row = QHBoxLayout(panel)
        self.chk_activar = QCheckBox()
        self.chk_activar.stateChanged.connect(self._guardar_preferencia)
        self.chk_activar_estimaciones = QCheckBox()
        self.chk_activar_estimaciones.stateChanged.connect(self._guardar_preferencia_estimaciones)
        row.addWidget(self.chk_activar)
        row.addWidget(self.chk_activar_estimaciones)
        row.addStretch(1)
        return panel
    def _comprobar_datos(self) -> None:
        self._actualizar_salud()
        self._actualizar_resultados_recientes()
        result = self._facade.comprobar_datos_uc.ejecutar()
        self._datos_aptos = result.apto_para_entrenar
        self.lbl_paso_1_estado.setText(self._i18n.t("prediccion_ausencias.paso_1.total").format(total=result.citas_validas))
        self.lbl_paso_1_mensaje.setText(self._i18n.t(result.mensaje_clave).format(minimo=result.minimo_requerido))
        if not self._entrenamiento_activo and not self._datos_aptos:
            self._set_estado_error("dataset_insuficiente")
        self._actualizar_estado_botones()
    def _actualizar_salud(self) -> None:
        salud = self._facade.obtener_salud_uc.ejecutar()
        self.lbl_salud_estado.setText(self._i18n.t(f"prediccion_ausencias.salud.estado.{salud.estado.lower()}"))
        self.lbl_salud_mensaje.setText(self._i18n.t(salud.mensaje_i18n_key).format(citas=salud.citas_validas_recientes))
        self.btn_salud_entrenar.setVisible(salud.estado in {"AMARILLO", "ROJO"})
        self._actualizar_banner_recordatorio(salud.estado)
        mostrar_cierre = salud.estado in {"AMARILLO", "ROJO"} and salud.citas_validas_recientes < 50
        self.btn_cerrar_citas_antiguas.setVisible(mostrar_cierre)
        self.lbl_salud_ayuda_cierre.setVisible(mostrar_cierre)
    def _actualizar_resultados_recientes(self) -> None:
        resultado = self._facade.obtener_resultados_recientes_uc.ejecutar(ventana_semanas=self._ventana_resultados_semanas)
        self.lbl_resultados_subtitulo.setText(self._i18n.t("prediccion_ausencias.resultados.subtitulo"))
        self.lbl_resultados_estado.setText(
            self._i18n.t("prediccion_ausencias.resultados.por_que").format(texto=self._i18n.t(resultado.por_que_i18n_key))
        )
        self.lbl_resultados_accion.setText(
            self._i18n.t("prediccion_ausencias.resultados.que_hacer").format(texto=self._i18n.t(resultado.que_hacer_i18n_key))
        )
        self._configurar_ctas_resultados(resultado.diagnostico)
        if resultado.diagnostico is not DiagnosticoResultadosRecientes.OK:
            self.lbl_resultado_bajo.setText("")
            self.lbl_resultado_medio.setText("")
            self.lbl_resultado_alto.setText("")
            return
        textos = {
            fila.riesgo: self._i18n.t("prediccion_ausencias.resultados.fila").format(
                riesgo=self._i18n.t(f"prediccion_ausencias.riesgo.{fila.riesgo.lower()}"),
                total=fila.total_predichas,
                no_vino=fila.total_no_vino,
            )
            for fila in resultado.filas
        }
        self.lbl_resultado_bajo.setText(textos.get("BAJO", ""))
        self.lbl_resultado_medio.setText(textos.get("MEDIO", ""))
        self.lbl_resultado_alto.setText(textos.get("ALTO", ""))

    def _on_cambio_periodo_resultados(self) -> None:
        semanas = self.cmb_resultados_periodo.currentData()
        if semanas is None:
            return
        self._ventana_resultados_semanas = int(semanas)
        self._guardar_preferencia_ventana_resultados()
        self.lbl_resultados_estado.setText(self._i18n.t("prediccion_ausencias.resultados.actualizando"))
        QTimer.singleShot(0, self._actualizar_resultados_recientes)

    def _mostrar_ayuda_resultados(self) -> None:
        bullets = [
            self._i18n.t("prediccion_ausencias.resultados.ayuda.bullet_1"),
            self._i18n.t("prediccion_ausencias.resultados.ayuda.bullet_2"),
            self._i18n.t("prediccion_ausencias.resultados.ayuda.bullet_3"),
        ]
        texto = "\n".join(f"• {item}" for item in bullets)
        QMessageBox.information(
            self,
            self._i18n.t("prediccion_ausencias.resultados.ayuda.titulo"),
            texto,
        )
    def _configurar_ctas_resultados(self, diagnostico: DiagnosticoResultadosRecientes) -> None:
        mostrar_cierre = diagnostico in {
            DiagnosticoResultadosRecientes.SIN_CITAS_CERRADAS,
            DiagnosticoResultadosRecientes.DATOS_INSUFICIENTES,
        }
        mostrar_confirmaciones = diagnostico in {
            DiagnosticoResultadosRecientes.SIN_PREDICCIONES_REGISTRADAS,
            DiagnosticoResultadosRecientes.DATOS_INSUFICIENTES,
        }
        mostrar_activar = diagnostico is DiagnosticoResultadosRecientes.SIN_PREDICCIONES_REGISTRADAS
        self.btn_resultados_cerrar_citas_antiguas.setVisible(mostrar_cierre)
        self.btn_resultados_abrir_confirmaciones.setVisible(mostrar_confirmaciones)
        self.btn_resultados_activar_riesgo_agenda.setVisible(mostrar_activar)
    def _on_cta_cerrar_citas_antiguas(self) -> None:
        self._log_cta_resultados("cerrar_citas_antiguas")
        self._abrir_asistente_cierre()
    def _on_cta_abrir_confirmaciones(self) -> None:
        self._log_cta_resultados("abrir_confirmaciones")
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate("confirmaciones")
    def _on_cta_activar_riesgo_agenda(self) -> None:
        self._log_cta_resultados("activar_riesgo_agenda")
        qsettings = QSettings("clinicdesk", "ui")
        try:
            qsettings.setValue(self._settings_key, 1)
            self.chk_activar.setChecked(True)
            QMessageBox.information(
                self,
                self._i18n.t("prediccion_ausencias.resultados.cta.activar_riesgo_agenda"),
                self._i18n.t("prediccion_ausencias.resultados.cta.activar_riesgo_ok"),
            )
        except Exception:  # noqa: BLE001
            LOGGER.exception(
                "resultados_recientes_cta_activar_riesgo_error",
                extra={"action": "resultados_recientes_cta", "cta_code": "activar_riesgo_agenda"},
            )
            QMessageBox.warning(
                self,
                self._i18n.t("prediccion_ausencias.resultados.cta.activar_riesgo_agenda"),
                self._i18n.t("prediccion_ausencias.resultados.cta.activar_riesgo_error"),
            )
    def _log_cta_resultados(self, cta_code: str) -> None:
        LOGGER.info(
            "resultados_recientes_cta",
            extra={"action": "resultados_recientes_cta", "cta_code": cta_code, "page": "prediccion_ausencias"},
        )
    def _on_entrenar_click(self) -> None:
        try:
            reason_code = self._validar_entrenamiento()
            LOGGER.info("prediccion_entrenar_click", extra={"action": "prediccion_entrenar_click", "page": "prediccion_ausencias", "reason_code": reason_code})
            if reason_code == "already_running":
                LOGGER.warning("prediccion_entrenar_click_ignored", extra={"action": "prediccion_entrenar_click_ignored", "reason_code": reason_code})
                return
            if reason_code is not None:
                self._set_estado_error(reason_code)
                return
            self._iniciar_entrenamiento_async()
        except Exception:  # noqa: BLE001
            LOGGER.exception("prediccion_entrenar_click_fail", extra={"action": "prediccion_entrenar_click_fail", "page": "prediccion_ausencias"})
            self._set_estado_error("unexpected_error")
    def _iniciar_entrenamiento_async(self) -> None:
        self._set_estado_running()
        thread = QThread(self)
        worker = EntrenarPrediccionWorker(self._facade.entrenar_uc, self._facade.proveedor_conexion)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.ok.connect(self._on_entrenar_ok)
        worker.fail.connect(self._on_entrenar_fail)
        worker.ok.connect(thread.quit)
        worker.fail.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_entrenar_finish)
        self._entrenar_thread = thread
        self._entrenar_worker = worker
        thread.start()
    def _validar_entrenamiento(self) -> str | None:
        if self._entrenamiento_activo:
            return "already_running"
        if not self._datos_aptos:
            return "dataset_insuficiente"
        return None
    def _on_entrenar_ok(self, resultado: ResultadoEntrenamientoPrediccion) -> None:
        try:
            self._set_estado_success()
            self._limpiar_recordatorio_por_entrenamiento()
            self._actualizar_salud()
            self._actualizar_resultados_recientes()
            self._cargar_previsualizacion()
            LOGGER.info("prediccion_entrenar_ok", extra={"action": "prediccion_entrenar_ok", "page": "prediccion_ausencias", "citas_usadas": resultado.citas_usadas, "fecha_metadata": resultado.fecha_entrenamiento})
        except Exception:  # noqa: BLE001
            LOGGER.exception("prediccion_entrenar_ok_handler_crash", extra={"action": "prediccion_entrenar_ok_handler_crash", "page": "prediccion_ausencias"})
            self._set_estado_error("unexpected_error")
    def _on_entrenar_fail(self, fail_payload: EntrenamientoFailPayload | str) -> None:
        error_ctx = self._normalizar_contexto_fallo(fail_payload)
        normalizado = normalizar_error_entrenamiento(error_ctx.reason_code)
        try:
            self._set_estado_error(normalizado.reason_code)
            self._escribir_incidente_fallo(
                reason_code=normalizado.reason_code,
                error_type=error_ctx.error_type,
                error_message=error_ctx.error_message,
            )
            LOGGER.error(
                "prediccion_entrenar_fail",
                extra={
                    "action": "prediccion_entrenar_fail",
                    "page": "prediccion_ausencias",
                    "reason_code": normalizado.reason_code,
                    "error_type": error_ctx.error_type,
                    "error_message": error_ctx.error_message,
                },
            )
        except Exception:  # noqa: BLE001
            LOGGER.exception(
                "prediccion_entrenar_fail_handler_crash",
                extra={"action": "prediccion_entrenar_fail_handler_crash", "page": "prediccion_ausencias"},
            )
            self._set_estado_error("unexpected_error")

    def _normalizar_contexto_fallo(self, fail_payload: EntrenamientoFailPayload | str) -> EntrenamientoFailPayload:
        if isinstance(fail_payload, EntrenamientoFailPayload):
            return fail_payload
        return EntrenamientoFailPayload(
            reason_code=str(fail_payload) if str(fail_payload).strip() else "unexpected_error",
            error_type="UnknownError",
            error_message=str(fail_payload),
        )

    def _escribir_incidente_fallo(self, *, reason_code: str, error_type: str, error_message: str) -> None:
        try:
            run_id, request_id = get_contexto_log()
            ruta = escribir_incidente_entrenamiento(
                Path("./logs"),
                run_id=run_id,
                request_id=request_id,
                reason_code=reason_code,
                error_type=error_type,
                error_message=error_message,
                stage="entrenar",
            )
            LOGGER.error(
                "prediccion_entrenar_incidente",
                extra={"action": "prediccion_entrenar_incidente", "reason_code": reason_code, "incident_path": str(ruta)},
            )
        except Exception:  # noqa: BLE001
            LOGGER.exception(
                "prediccion_entrenar_incidente_fail",
                extra={"action": "prediccion_entrenar_incidente_fail", "reason_code": reason_code},
            )
    def _on_entrenar_finish(self) -> None:
        self._entrenamiento_activo = False
        self._actualizar_estado_botones()
        self._entrenar_worker = None
        self._entrenar_thread = None
    def _set_estado_running(self) -> None:
        self._entrenamiento_activo = True
        self.lbl_paso_2_estado.setText(self._i18n.t("prediccion.entrenar.en_curso"))
        self.progress_entrenamiento.setVisible(True)
        self.btn_reintentar.setVisible(False)
        self._actualizar_estado_botones()
    def _set_estado_success(self) -> None:
        self.lbl_paso_2_estado.setText(self._i18n.t("prediccion.entrenar.ok"))
        self.progress_entrenamiento.setVisible(False)
        self.btn_reintentar.setVisible(False)
    def _set_estado_error(self, reason_code: str) -> None:
        normalizado = normalizar_error_entrenamiento(reason_code)
        self.lbl_paso_2_estado.setText(self._i18n.t(normalizado.mensaje_i18n_key))
        self.progress_entrenamiento.setVisible(False)
        self.btn_reintentar.setVisible(normalizado.reason_code not in {"dataset_insuficiente", "dataset_empty"})
    def _actualizar_estado_botones(self) -> None:
        habilitar = (not self._entrenamiento_activo) and self._datos_aptos
        self.btn_entrenar.setEnabled(habilitar)
        self.btn_salud_entrenar.setEnabled(habilitar)
    def _cargar_previsualizacion(self) -> None:
        result = self._facade.previsualizar_uc.ejecutar(limite=30)
        if result.estado == "SIN_MODELO":
            self.lbl_paso_3_estado.setText(self._i18n.t("prediccion_ausencias.estado.sin_modelo"))
            self.tabla.setRowCount(0)
            return
        if result.estado == "ERROR":
            self.lbl_paso_3_estado.setText(self._i18n.t("prediccion_ausencias.estado.carga_error"))
            self.tabla.setRowCount(0)
            return
        self.lbl_paso_3_estado.setText(self._i18n.t("prediccion_ausencias.estado.previsualizacion_lista"))
        self.tabla.setRowCount(len(result.items))
        for row, item in enumerate(result.items):
            values = [item.fecha, item.hora, item.paciente, item.medico, self._i18n.t(f"prediccion_ausencias.riesgo.{item.riesgo.lower()}"),]
            for col, value in enumerate(values):
                self.tabla.setItem(row, col, QTableWidgetItem(value))
    def _guardar_preferencia(self, state: int) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        qsettings.setValue(self._settings_key, 1 if state == Qt.Checked else 0)
    def _guardar_preferencia_estimaciones(self, state: int) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        qsettings.setValue(self._settings_estimaciones_key, 1 if state == Qt.Checked else 0)

    def _restaurar_preferencia(self) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        checked = bool(int(qsettings.value(self._settings_key, 0)))
        self.chk_activar.setChecked(checked)
        checked_estimaciones = bool(int(qsettings.value(self._settings_estimaciones_key, 0)))
        self.chk_activar_estimaciones.setChecked(checked_estimaciones)
        self._restaurar_preferencia_ventana_resultados()
        self._preferencia_recordatorio = leer_preferencia_recordatorio_entrenar(qsettings)

    def _guardar_preferencia_ventana_resultados(self) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        qsettings.setValue(
            CLAVE_VENTANA_RESULTADOS_RECIENTES,
            serializar_ventana_resultados_semanas(self._ventana_resultados_semanas),
        )

    def _restaurar_preferencia_ventana_resultados(self) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        valor = qsettings.value(
            CLAVE_VENTANA_RESULTADOS_RECIENTES,
            serializar_ventana_resultados_semanas(VENTANA_RESULTADOS_POR_DEFECTO),
        )
        self._ventana_resultados_semanas = deserializar_ventana_resultados_semanas(valor)
        self._recargar_opciones_periodo()

    def _actualizar_banner_recordatorio(self, salud_estado: str) -> None:
        if self._recordatorio_oculto_sesion:
            self.banner_recordatorio.setVisible(False)
            return
        hoy_utc = date.today()
        fecha = self._preferencia_recordatorio.fecha_recordatorio_utc
        if not debe_mostrar_recordatorio(hoy_utc, salud_estado, fecha):
            self.banner_recordatorio.setVisible(False)
            return
        motivo = "first" if fecha is None else "due"
        texto_clave = (
            "prediccion_ausencias.recordatorio.texto.primer_aviso"
            if motivo == "first"
            else "prediccion_ausencias.recordatorio.texto.vencido"
        )
        if self._ultimo_motivo_recordatorio_log != motivo:
            LOGGER.info(
                "prediccion_recordatorio_mostrar",
                extra={"action": "prediccion_recordatorio_mostrar", "motivo": motivo},
            )
            self._ultimo_motivo_recordatorio_log = motivo
        self.lbl_recordatorio.setText(self._i18n.t(texto_clave))
        self.banner_recordatorio.setVisible(True)

    def _on_recordatorio_mas_tarde(self) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        self._preferencia_recordatorio = posponer_recordatorio_entrenar(
            qsettings,
            hoy_utc=date.today(),
            dias_snooze=self._preferencia_recordatorio.dias_snooze,
        )
        self._recordatorio_oculto_sesion = True
        self.banner_recordatorio.setVisible(False)
        LOGGER.info(
            "prediccion_recordatorio_snooze",
            extra={
                "action": "prediccion_recordatorio_snooze",
                "dias": self._preferencia_recordatorio.dias_snooze,
            },
        )

    def _limpiar_recordatorio_por_entrenamiento(self) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        limpiar_recordatorio_entrenar(qsettings, dias_snooze=self._preferencia_recordatorio.dias_snooze)
        self._preferencia_recordatorio = leer_preferencia_recordatorio_entrenar(qsettings)
        self._recordatorio_oculto_sesion = False
        self._ultimo_motivo_recordatorio_log = None
        LOGGER.info("prediccion_recordatorio_clear", extra={"action": "prediccion_recordatorio_clear"})

    def _retranslate(self) -> None:
        self.box_salud.setTitle(self._i18n.t("prediccion_ausencias.salud.titulo"))
        self.box_resultados.setTitle(self._i18n.t("prediccion_ausencias.resultados.titulo"))
        self.box_paso_1.setTitle(self._i18n.t("prediccion_ausencias.paso_1.titulo"))
        self.box_paso_2.setTitle(self._i18n.t("prediccion_ausencias.paso_2.titulo"))
        self.box_paso_3.setTitle(self._i18n.t("prediccion_ausencias.paso_3.titulo"))
        self.btn_salud_entrenar.setText(self._i18n.t("prediccion_ausencias.accion.entrenar"))
        self.btn_recordatorio_entrenar.setText(self._i18n.t("prediccion_ausencias.accion.entrenar"))
        self.btn_recordatorio_mas_tarde.setText(
            self._i18n.t("prediccion_ausencias.recordatorio.accion.mas_tarde").format(
                dias=self._preferencia_recordatorio.dias_snooze
            )
        )
        self.btn_entrenar.setText(self._i18n.t("prediccion_ausencias.accion.entrenar"))
        self.btn_reintentar.setText(self._i18n.t("prediccion.entrenar.reintentar"))
        self.chk_activar.setText(self._i18n.t("prediccion_ausencias.accion.activar_agenda"))
        self.chk_activar_estimaciones.setText(self._i18n.t("citas.prediccion_operativa.toggle.mostrar_estimaciones"))
        self.btn_cerrar_citas_antiguas.setText(self._i18n.t("prediccion_ausencias.cierre.cta"))
        self.lbl_salud_ayuda_cierre.setText(self._i18n.t("prediccion_ausencias.cierre.cta_ayuda"))
        self.btn_resultados_cerrar_citas_antiguas.setText(self._i18n.t("prediccion_ausencias.resultados.cta.cerrar_citas_antiguas"))
        self.btn_resultados_abrir_confirmaciones.setText(self._i18n.t("prediccion_ausencias.resultados.cta.abrir_confirmaciones"))
        self.btn_resultados_activar_riesgo_agenda.setText(self._i18n.t("prediccion_ausencias.resultados.cta.activar_riesgo_agenda"))
        self.lbl_resultados_periodo.setText(self._i18n.t("prediccion_ausencias.resultados.periodo"))
        self.btn_resultados_ayuda.setText(self._i18n.t("prediccion_ausencias.resultados.ayuda.accion"))
        self._recargar_opciones_periodo()
        self.tabla.setHorizontalHeaderLabels([self._i18n.t("prediccion_ausencias.tabla.fecha"), self._i18n.t("prediccion_ausencias.tabla.hora"), self._i18n.t("prediccion_ausencias.tabla.paciente"), self._i18n.t("prediccion_ausencias.tabla.medico"), self._i18n.t("prediccion_ausencias.tabla.riesgo")])
        self._actualizar_resultados_recientes()

    def _recargar_opciones_periodo(self) -> None:
        self.cmb_resultados_periodo.blockSignals(True)
        self.cmb_resultados_periodo.clear()
        opciones = (
            (4, self._i18n.t("prediccion_ausencias.resultados.periodo.4")),
            (8, self._i18n.t("prediccion_ausencias.resultados.periodo.8")),
            (12, self._i18n.t("prediccion_ausencias.resultados.periodo.12")),
        )
        for semanas, etiqueta in opciones:
            self.cmb_resultados_periodo.addItem(etiqueta, semanas)
        indice = self.cmb_resultados_periodo.findData(self._ventana_resultados_semanas)
        self.cmb_resultados_periodo.setCurrentIndex(max(0, indice))
        self.cmb_resultados_periodo.blockSignals(False)
    def _abrir_asistente_cierre(self) -> None:
        dialog = CerrarCitasAntiguasDialog(self._facade, self._i18n, self)
        if dialog.exec():
            self._actualizar_salud()
            self._actualizar_resultados_recientes()
            self._comprobar_datos()
