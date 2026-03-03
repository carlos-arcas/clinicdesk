from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.services.prediccion_operativa_facade import PrediccionOperativaFacade
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.prediccion_operativa.helpers import (
    construir_bullets_explicacion,
    debe_cargar_previsualizacion,
    resolver_clave_estado_salud,
    resolver_texto_estimacion,
)
from clinicdesk.app.pages.prediccion_operativa.workers import WorkerEntrenarOperativo
from clinicdesk.app.pages.shared.persistencia_estimaciones_settings import (
    guardar_mostrar_estimaciones_agenda,
    leer_mostrar_estimaciones_agenda,
)


@dataclass(slots=True)
class _RefsBloque:
    tipo: str
    box: QGroupBox
    lbl_estado: QLabel
    lbl_actualizacion: QLabel
    lbl_datos: QLabel
    lbl_feedback: QLabel
    btn_comprobar: QPushButton
    btn_preparar: QPushButton
    btn_reintentar: QPushButton
    progress: QProgressBar
    tabla: QTableWidget


class PagePrediccionOperativa(QWidget):
    def __init__(self, facade: PrediccionOperativaFacade, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
        self._i18n = i18n
        self._thread_duracion: QThread | None = None
        self._thread_espera: QThread | None = None
        self._worker_duracion: WorkerEntrenarOperativo | None = None
        self._worker_espera: WorkerEntrenarOperativo | None = None
        self._predicciones_duracion: dict[int, str] = {}
        self._predicciones_espera: dict[int, str] = {}
        self._proximas_citas: list[object] = []
        self._build_ui()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()

    def on_show(self) -> None:
        self._refresh_todo()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        self.lbl_titulo = QLabel()
        self.chk_mostrar_agenda = QCheckBox()
        self.chk_mostrar_agenda.stateChanged.connect(self._on_toggle_changed)
        root.addWidget(self.lbl_titulo)
        root.addWidget(self.chk_mostrar_agenda)
        self._bloque_duracion = self._crear_bloque("duracion")
        self._bloque_espera = self._crear_bloque("espera")
        root.addWidget(self._bloque_duracion.box)
        root.addWidget(self._bloque_espera.box)

    def _crear_bloque(self, tipo: str) -> _RefsBloque:
        box = QGroupBox()
        layout = QVBoxLayout(box)
        lbl_estado = QLabel()
        lbl_actualizacion = QLabel()
        lbl_datos = QLabel()
        lbl_feedback = QLabel()
        lbl_feedback.setWordWrap(True)
        btn_comprobar = QPushButton()
        btn_preparar = QPushButton()
        btn_reintentar = QPushButton()
        btn_reintentar.setVisible(False)
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setVisible(False)
        tabla = QTableWidget(0, 6)
        tabla.horizontalHeader().setStretchLastSection(True)
        btn_comprobar.clicked.connect(lambda: self._comprobar_datos(tipo))
        btn_preparar.clicked.connect(lambda: self._entrenar(tipo))
        btn_reintentar.clicked.connect(lambda: self._entrenar(tipo))
        for widget in (lbl_estado, lbl_actualizacion, btn_comprobar, lbl_datos, btn_preparar, lbl_feedback, progress, btn_reintentar, tabla):
            layout.addWidget(widget)
        return _RefsBloque(tipo, box, lbl_estado, lbl_actualizacion, lbl_datos, lbl_feedback, btn_comprobar, btn_preparar, btn_reintentar, progress, tabla)

    def _refresh_todo(self) -> None:
        self.chk_mostrar_agenda.setChecked(leer_mostrar_estimaciones_agenda())
        self._proximas_citas = self._facade.listar_proximas_citas_uc.ejecutar(30, 30)
        self._comprobar_datos("duracion")
        self._comprobar_datos("espera")
        self._cargar_previsualizacion()

    def _comprobar_datos(self, tipo: str) -> None:
        bloque = self._bloque(tipo)
        uc = self._facade.comprobar_duracion_uc if tipo == "duracion" else self._facade.comprobar_espera_uc
        salud_uc = self._facade.salud_duracion_uc if tipo == "duracion" else self._facade.salud_espera_uc
        datos = uc.ejecutar()
        salud = salud_uc.ejecutar()
        bloque.lbl_datos.setText(self._i18n.t("prediccion_operativa.paso_1.encontradas").format(total=datos.ejemplos_validos))
        bloque.lbl_estado.setText(self._i18n.t(resolver_clave_estado_salud(salud.estado)))
        fecha = salud.fecha_ultima_actualizacion or self._i18n.t("prediccion_operativa.estado.no_disponible")
        bloque.lbl_actualizacion.setText(self._i18n.t("prediccion_operativa.estado.ultima_actualizacion").format(fecha=fecha))
        if not datos.apto_para_entrenar:
            bloque.lbl_feedback.setText(self._i18n.t("prediccion_operativa.msg.faltan_datos"))

    def _entrenar(self, tipo: str) -> None:
        bloque = self._bloque(tipo)
        bloque.progress.setVisible(True)
        bloque.btn_preparar.setEnabled(False)
        bloque.btn_comprobar.setEnabled(False)
        bloque.btn_reintentar.setVisible(False)
        bloque.lbl_feedback.setText(self._i18n.t("prediccion_operativa.estado.actualizando"))
        self._ejecutar_worker(tipo)

    def _ejecutar_worker(self, tipo: str) -> None:
        thread = QThread()
        uc = self._facade.entrenar_duracion_uc if tipo == "duracion" else self._facade.entrenar_espera_uc
        worker = WorkerEntrenarOperativo(uc.ejecutar, self._facade.cerrar_conexion_hilo_actual)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.ok.connect(lambda _: self._on_train_ok(tipo))
        worker.fail.connect(lambda _: self._on_train_fail(tipo))
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        if tipo == "duracion":
            self._thread_duracion, self._worker_duracion = thread, worker
        else:
            self._thread_espera, self._worker_espera = thread, worker
        thread.start()

    def _on_train_ok(self, tipo: str) -> None:
        bloque = self._bloque(tipo)
        bloque.progress.setVisible(False)
        bloque.lbl_feedback.setText(self._i18n.t("prediccion_operativa.msg.listo"))
        bloque.btn_preparar.setEnabled(True)
        bloque.btn_comprobar.setEnabled(True)
        self._comprobar_datos(tipo)
        self._cargar_previsualizacion()

    def _on_train_fail(self, tipo: str) -> None:
        bloque = self._bloque(tipo)
        bloque.progress.setVisible(False)
        bloque.lbl_feedback.setText(self._i18n.t("prediccion_operativa.msg.error_preparar"))
        bloque.btn_reintentar.setVisible(True)
        bloque.btn_preparar.setEnabled(True)
        bloque.btn_comprobar.setEnabled(True)

    def _cargar_previsualizacion(self) -> None:
        if not debe_cargar_previsualizacion(self.chk_mostrar_agenda.isChecked()):
            self._vaciar_tablas()
            return
        self._predicciones_duracion = {k: v.nivel for k, v in self._facade.previsualizar_duracion_uc.ejecutar(30).items()}
        self._predicciones_espera = {k: v.nivel for k, v in self._facade.previsualizar_espera_uc.ejecutar(30).items()}
        self._render_tabla(self._bloque_duracion, self._predicciones_duracion)
        self._render_tabla(self._bloque_espera, self._predicciones_espera)

    def _render_tabla(self, bloque: _RefsBloque, predicciones: dict[int, str]) -> None:
        tabla = bloque.tabla
        tabla.setRowCount(0)
        for cita in self._proximas_citas:
            fila = tabla.rowCount()
            tabla.insertRow(fila)
            nivel = predicciones.get(cita.cita_id, "NO_DISPONIBLE")
            valores = [cita.fecha, cita.hora, cita.paciente, cita.medico, resolver_texto_estimacion(nivel, self._i18n)]
            for col, valor in enumerate(valores):
                tabla.setItem(fila, col, QTableWidgetItem(str(valor)))
            boton = QPushButton(self._i18n.t("prediccion_operativa.btn.ver_por_que"))
            boton.clicked.connect(lambda _, c=cita.cita_id, n=nivel, t=bloque.tipo: self._mostrar_por_que(t, c, n))
            tabla.setCellWidget(fila, 5, boton)
        if tabla.rowCount() == 0:
            bloque.lbl_feedback.setText(self._i18n.t("prediccion_operativa.msg.sin_proximas"))

    def _mostrar_por_que(self, tipo: str, cita_id: int, nivel: str) -> None:
        uc = self._facade.explicar_duracion_uc if tipo == "duracion" else self._facade.explicar_espera_uc
        exp = uc.ejecutar(cita_id, nivel)
        QMessageBox.information(self, self._i18n.t("prediccion_operativa.btn.ver_por_que"), construir_bullets_explicacion(exp, self._i18n))

    def _vaciar_tablas(self) -> None:
        for bloque in (self._bloque_duracion, self._bloque_espera):
            bloque.tabla.setRowCount(0)
            bloque.lbl_feedback.setText(self._i18n.t("prediccion_operativa.msg.sin_proximas"))

    def _bloque(self, tipo: str) -> _RefsBloque:
        return self._bloque_duracion if tipo == "duracion" else self._bloque_espera

    def _on_toggle_changed(self, state: int) -> None:
        guardar_mostrar_estimaciones_agenda(state == Qt.Checked)
        self._cargar_previsualizacion()

    def _retranslate(self) -> None:
        self.lbl_titulo.setText(self._i18n.t("prediccion_operativa.titulo"))
        self.chk_mostrar_agenda.setText(self._i18n.t("citas.prediccion_operativa.toggle.mostrar_estimaciones"))
        self._traducir_bloque(self._bloque_duracion, "prediccion_operativa.duracion")
        self._traducir_bloque(self._bloque_espera, "prediccion_operativa.espera")

    def _traducir_bloque(self, bloque: _RefsBloque, titulo_key: str) -> None:
        bloque.box.setTitle(self._i18n.t(titulo_key))
        bloque.btn_comprobar.setText(self._i18n.t("prediccion_operativa.btn.comprobar_datos"))
        bloque.btn_preparar.setText(self._i18n.t("prediccion_operativa.btn.preparar_ahora"))
        bloque.btn_reintentar.setText(self._i18n.t("prediccion_operativa.btn.reintentar"))
        bloque.tabla.setHorizontalHeaderLabels(
            [
                self._i18n.t("prediccion_operativa.tabla.fecha"),
                self._i18n.t("prediccion_operativa.tabla.hora"),
                self._i18n.t("prediccion_operativa.tabla.paciente"),
                self._i18n.t("prediccion_operativa.tabla.medico"),
                self._i18n.t("prediccion_operativa.tabla.estimacion"),
                self._i18n.t("prediccion_operativa.tabla.accion"),
            ]
        )
