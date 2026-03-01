from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
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
)

from clinicdesk.app.application.prediccion_ausencias import ResultadoEntrenamientoPrediccion
from clinicdesk.app.application.services.prediccion_ausencias_facade import PrediccionAusenciasFacade
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.prediccion_ausencias.cerrar_citas_antiguas_dialog import CerrarCitasAntiguasDialog
from clinicdesk.app.pages.prediccion_ausencias.entrenar_worker import RunnerEntrenamientoPrediccion

LOGGER = get_logger(__name__)


class PagePrediccionAusencias(QWidget):
    def __init__(self, facade: PrediccionAusenciasFacade, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
        self._i18n = i18n
        self._datos_aptos = False
        self._entrenamiento_activo = False
        self._runner_entrenamiento: RunnerEntrenamientoPrediccion | None = None
        self._settings_key = "prediccion_ausencias/mostrar_riesgo_agenda"
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
        self.btn_salud_entrenar.clicked.connect(self._entrenar)
        self.lbl_salud_ayuda_cierre = QLabel()
        self.lbl_salud_ayuda_cierre.setWordWrap(True)
        self.btn_cerrar_citas_antiguas = QPushButton()
        self.btn_cerrar_citas_antiguas.clicked.connect(self._abrir_asistente_cierre)
        layout.addWidget(self.lbl_salud_estado)
        layout.addWidget(self.lbl_salud_mensaje)
        layout.addWidget(self.btn_salud_entrenar)
        layout.addWidget(self.btn_cerrar_citas_antiguas)
        layout.addWidget(self.lbl_salud_ayuda_cierre)
        return self.box_salud

    def _build_resultados_recientes(self) -> QWidget:
        self.box_resultados = QGroupBox()
        layout = QVBoxLayout(self.box_resultados)
        self.lbl_resultados_subtitulo = QLabel()
        self.lbl_resultados_subtitulo.setWordWrap(True)
        self.lbl_resultados_estado = QLabel()
        self.lbl_resultados_estado.setWordWrap(True)
        self.lbl_resultados_accion = QLabel()
        self.lbl_resultados_accion.setWordWrap(True)
        self.lbl_resultado_bajo = QLabel()
        self.lbl_resultado_medio = QLabel()
        self.lbl_resultado_alto = QLabel()
        layout.addWidget(self.lbl_resultados_subtitulo)
        layout.addWidget(self.lbl_resultados_estado)
        layout.addWidget(self.lbl_resultados_accion)
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
        self.btn_entrenar.clicked.connect(self._entrenar)
        self.lbl_paso_2_estado = QLabel()
        self.lbl_paso_2_estado.setWordWrap(True)
        self.progress_entrenamiento = QProgressBar()
        self.progress_entrenamiento.setRange(0, 0)
        self.progress_entrenamiento.setVisible(False)
        self.btn_reintentar = QPushButton()
        self.btn_reintentar.clicked.connect(self._entrenar)
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
        row.addWidget(self.chk_activar)
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
        mostrar_cierre = salud.estado in {"AMARILLO", "ROJO"} and salud.citas_validas_recientes < 50
        self.btn_cerrar_citas_antiguas.setVisible(mostrar_cierre)
        self.lbl_salud_ayuda_cierre.setVisible(mostrar_cierre)

    def _actualizar_resultados_recientes(self) -> None:
        resultado = self._facade.obtener_resultados_recientes_uc.ejecutar()
        semanas = max(1, resultado.ventana_dias // 7)
        self.lbl_resultados_subtitulo.setText(self._i18n.t("prediccion_ausencias.resultados.subtitulo").format(semanas=semanas))
        self.lbl_resultados_estado.setText(self._i18n.t(resultado.mensaje_i18n_key))
        self.lbl_resultados_accion.setText(" ".join(self._i18n.t(key) for key in resultado.acciones_i18n_keys))
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

    def _entrenar(self) -> None:
        reason_code = self._validar_entrenamiento()
        LOGGER.info("prediccion_entrenar_click", extra={"action": "prediccion_entrenar_click", "page": "prediccion_ausencias", "reason_code": reason_code})
        if reason_code is not None:
            self._set_estado_error(reason_code)
            return
        self._set_estado_running()
        self._runner_entrenamiento = RunnerEntrenamientoPrediccion(self._facade.entrenar_uc)
        self._runner_entrenamiento.success.connect(self._on_entrenar_ok)
        self._runner_entrenamiento.error.connect(self._on_entrenar_fail)
        self._runner_entrenamiento.finished.connect(self._on_entrenar_finish)
        self._runner_entrenamiento.start()

    def _validar_entrenamiento(self) -> str | None:
        if self._entrenamiento_activo:
            return "already_running"
        if not self._datos_aptos:
            return "dataset_insuficiente"
        return None

    def _on_entrenar_ok(self, resultado: ResultadoEntrenamientoPrediccion) -> None:
        self._set_estado_success()
        self._actualizar_salud()
        self._actualizar_resultados_recientes()
        self._cargar_previsualizacion()
        LOGGER.info("prediccion_entrenar_ok", extra={"action": "prediccion_entrenar_ok", "page": "prediccion_ausencias", "citas_usadas": resultado.citas_usadas, "fecha_metadata": resultado.fecha_entrenamiento})

    def _on_entrenar_fail(self, reason_code: str) -> None:
        self._set_estado_error(reason_code)
        LOGGER.error("prediccion_entrenar_fail", extra={"action": "prediccion_entrenar_fail", "page": "prediccion_ausencias", "reason_code": reason_code})

    def _on_entrenar_finish(self) -> None:
        self._entrenamiento_activo = False
        self._actualizar_estado_botones()
        self._runner_entrenamiento = None

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
        key = "prediccion.entrenar.error"
        if reason_code == "dataset_insuficiente":
            key = "prediccion.entrenar.bloqueado_por_datos"
        self.lbl_paso_2_estado.setText(self._i18n.t(key))
        self.progress_entrenamiento.setVisible(False)
        self.btn_reintentar.setVisible(reason_code != "dataset_insuficiente")

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

    def _restaurar_preferencia(self) -> None:
        qsettings = QSettings("clinicdesk", "ui")
        checked = bool(int(qsettings.value(self._settings_key, 0)))
        self.chk_activar.setChecked(checked)

    def _retranslate(self) -> None:
        self.box_salud.setTitle(self._i18n.t("prediccion_ausencias.salud.titulo"))
        self.box_resultados.setTitle(self._i18n.t("prediccion_ausencias.resultados.titulo"))
        self.box_paso_1.setTitle(self._i18n.t("prediccion_ausencias.paso_1.titulo"))
        self.box_paso_2.setTitle(self._i18n.t("prediccion_ausencias.paso_2.titulo"))
        self.box_paso_3.setTitle(self._i18n.t("prediccion_ausencias.paso_3.titulo"))
        self.btn_salud_entrenar.setText(self._i18n.t("prediccion_ausencias.accion.entrenar"))
        self.btn_entrenar.setText(self._i18n.t("prediccion_ausencias.accion.entrenar"))
        self.btn_reintentar.setText(self._i18n.t("prediccion.entrenar.reintentar"))
        self.chk_activar.setText(self._i18n.t("prediccion_ausencias.accion.activar_agenda"))
        self.btn_cerrar_citas_antiguas.setText(self._i18n.t("prediccion_ausencias.cierre.cta"))
        self.lbl_salud_ayuda_cierre.setText(self._i18n.t("prediccion_ausencias.cierre.cta_ayuda"))
        self.tabla.setHorizontalHeaderLabels([self._i18n.t("prediccion_ausencias.tabla.fecha"), self._i18n.t("prediccion_ausencias.tabla.hora"), self._i18n.t("prediccion_ausencias.tabla.paciente"), self._i18n.t("prediccion_ausencias.tabla.medico"), self._i18n.t("prediccion_ausencias.tabla.riesgo")])
        self._actualizar_resultados_recientes()

    def _abrir_asistente_cierre(self) -> None:
        dialog = CerrarCitasAntiguasDialog(self._facade, self._i18n, self)
        if dialog.exec():
            self._actualizar_salud()
            self._actualizar_resultados_recientes()
            self._comprobar_datos()
