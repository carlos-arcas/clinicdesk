from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.usecases.dashboard_gestion import (
    FiltrosDashboardDTO,
    ObtenerDashboardGestion,
    PRESET_30_DIAS,
    PRESET_7_DIAS,
    PRESET_HOY,
    PRESET_PERSONALIZADO,
)
from clinicdesk.app.application.usecases.dashboard_gestion_prediccion import CitaVigilarDTO
from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO
from clinicdesk.app.application.usecases.obtener_metricas_operativas import ObtenerMetricasOperativas
from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.gestion.adapters import PrediccionAusenciasGestionAdapter, PrediccionOperativaGestionAdapter
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.queries.dashboard_gestion_queries import DashboardGestionQueries
from clinicdesk.app.queries.metricas_operativas_queries import MetricasOperativasQueries


class PageGestionDashboard(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        metricas_uc = ObtenerMetricasOperativas(MetricasOperativasQueries(container.connection))
        self._use_case = ObtenerDashboardGestion(
            metricas_uc,
            PrediccionAusenciasGestionAdapter(container),
            PrediccionOperativaGestionAdapter(container),
            DashboardGestionQueries(container.connection),
        )
        self._build_ui()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()

    def on_show(self) -> None:
        self._cargar_dashboard()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addLayout(self._build_filtros())
        root.addWidget(self._build_prediccion())
        root.addLayout(self._build_kpis())
        root.addWidget(self._build_alertas())
        root.addWidget(self._build_tabla_medicos())
        root.addWidget(self._build_tabla_vigilancia())

    def _build_filtros(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.cmb_preset = QComboBox()
        self.cmb_preset.currentIndexChanged.connect(self._on_cambio_preset)
        self.date_desde = QDateEdit(QDate.currentDate())
        self.date_hasta = QDateEdit(QDate.currentDate())
        for edit in (self.date_desde, self.date_hasta):
            edit.setCalendarPopup(True)
            edit.dateChanged.connect(lambda _: self._forzar_personalizado())
        self.btn_actualizar = QPushButton()
        self.btn_actualizar.clicked.connect(self._cargar_dashboard)
        layout.addWidget(self.cmb_preset)
        layout.addWidget(self.date_desde)
        layout.addWidget(self.date_hasta)
        layout.addWidget(self.btn_actualizar)
        return layout

    def _build_prediccion(self) -> QGroupBox:
        box = QGroupBox()
        lay = QGridLayout(box)
        self.lbl_prediccion_titulo = QLabel()
        lay.addWidget(self.lbl_prediccion_titulo, 0, 0, 1, 3)
        self._estado_labels = [QLabel("-"), QLabel("-"), QLabel("-")]
        self._estado_titulos = [QLabel(), QLabel(), QLabel()]
        self.btn_ir_ausencias = QPushButton()
        self.btn_ir_estimaciones_duracion = QPushButton()
        self.btn_ir_estimaciones_espera = QPushButton()
        self.btn_ir_ausencias.clicked.connect(lambda: self._navegar_a("prediccion_ausencias"))
        self.btn_ir_estimaciones_duracion.clicked.connect(lambda: self._navegar_a("prediccion_operativa"))
        self.btn_ir_estimaciones_espera.clicked.connect(lambda: self._navegar_a("prediccion_operativa"))
        botones = [self.btn_ir_ausencias, self.btn_ir_estimaciones_duracion, self.btn_ir_estimaciones_espera]
        for idx, boton in enumerate(botones):
            lay.addWidget(self._estado_titulos[idx], idx + 1, 0)
            lay.addWidget(self._estado_labels[idx], idx + 1, 1)
            lay.addWidget(boton, idx + 1, 2)
        return box

    def _build_kpis(self) -> QGridLayout:
        layout = QGridLayout()
        self.lbl_total_citas = QLabel("-")
        self.lbl_espera = QLabel("-")
        self.lbl_duracion = QLabel("-")
        self.lbl_retraso = QLabel("-")
        self._kpi_titles = [QLabel(), QLabel(), QLabel(), QLabel()]
        for idx, (titulo, valor) in enumerate(zip(self._kpi_titles, [self.lbl_total_citas, self.lbl_espera, self.lbl_duracion, self.lbl_retraso], strict=True)):
            box = QGroupBox()
            form = QFormLayout(box)
            form.addRow(titulo, valor)
            layout.addWidget(box, idx // 2, idx % 2)
        return layout

    def _build_alertas(self) -> QGroupBox:
        box = QGroupBox()
        lay = QVBoxLayout(box)
        self.lbl_estado = QLabel()
        self.lbl_alertas = QLabel()
        self.lbl_alertas.setWordWrap(True)
        lay.addWidget(self.lbl_estado)
        lay.addWidget(self.lbl_alertas)
        self.btn_reintentar = QPushButton()
        self.btn_reintentar.clicked.connect(self._cargar_dashboard)
        lay.addWidget(self.btn_reintentar)
        return box

    def _build_tabla_medicos(self) -> QTableWidget:
        self.tabla_medicos = QTableWidget(0, 5)
        self.tabla_medicos.horizontalHeader().setStretchLastSection(True)
        return self.tabla_medicos

    def _build_tabla_vigilancia(self) -> QGroupBox:
        box = QGroupBox()
        lay = QVBoxLayout(box)
        self.lbl_sin_vigilancia = QLabel()
        self.tabla_vigilancia = QTableWidget(0, 5)
        self.tabla_vigilancia.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.lbl_sin_vigilancia)
        lay.addWidget(self.tabla_vigilancia)
        return box

    def _on_cambio_preset(self) -> None:
        preset = self.cmb_preset.currentData()
        habilitado = preset == PRESET_PERSONALIZADO
        self.date_desde.setEnabled(habilitado)
        self.date_hasta.setEnabled(habilitado)

    def _forzar_personalizado(self) -> None:
        if self.cmb_preset.currentData() != PRESET_PERSONALIZADO:
            self.cmb_preset.setCurrentIndex(3)

    def _cargar_dashboard(self) -> None:
        self.lbl_estado.setText(self._i18n.t("dashboard_gestion.estado.cargando"))
        self.lbl_alertas.setText("")
        try:
            resultado = self._use_case.execute(self._leer_filtros())
        except ValidationError:
            self._mostrar_error(self._i18n.t("dashboard_gestion.estado.error"))
            return
        self._render_resultado(resultado)

    def _leer_filtros(self) -> FiltrosDashboardDTO:
        return FiltrosDashboardDTO(
            preset=str(self.cmb_preset.currentData() or PRESET_7_DIAS),
            desde=self.date_desde.date().toPython(),
            hasta=self.date_hasta.date().toPython(),
        )

    def _render_resultado(self, resultado) -> None:
        self.lbl_total_citas.setText(str(resultado.kpis_resumen.total_citas))
        self.lbl_espera.setText(self._fmt_min(resultado.kpis_resumen.espera_media_min))
        self.lbl_duracion.setText(self._fmt_min(resultado.kpis_resumen.duracion_media_consulta_min))
        self.lbl_retraso.setText(self._fmt_min(resultado.kpis_resumen.retraso_media_min))
        self._render_estados_prediccion(resultado.estados_prediccion)
        self._render_alertas(resultado.alertas, resultado.kpis_resumen.total_citas)
        self._render_tabla_medicos(resultado.top_medicos)
        self._render_tabla_vigilancia(resultado.citas_a_vigilar)

    def _render_estados_prediccion(self, estados) -> None:
        self._estado_labels[0].setText(self._i18n.t(estados.salud_ausencias.label_i18n_key))
        self._estado_labels[1].setText(self._i18n.t(estados.salud_duracion.label_i18n_key))
        self._estado_labels[2].setText(self._i18n.t(estados.salud_espera.label_i18n_key))

    def _render_alertas(self, alertas: tuple, total_citas: int) -> None:
        if total_citas == 0:
            self.lbl_estado.setText(self._i18n.t("dashboard_gestion.estado.vacio"))
            self.lbl_alertas.setText("")
            return
        self.lbl_estado.setText(self._i18n.t("dashboard_gestion.estado.listo"))
        if not alertas:
            self.lbl_alertas.setText(self._i18n.t("dashboard_gestion.alerta.todo_en_orden"))
            return
        textos = [f"• {self._i18n.t(alerta.i18n_key)}" for alerta in alertas]
        self.lbl_alertas.setText("\n".join(textos))

    def _render_tabla_medicos(self, top_medicos: tuple) -> None:
        self.tabla_medicos.setRowCount(0)
        for medico in top_medicos:
            fila = self.tabla_medicos.rowCount()
            self.tabla_medicos.insertRow(fila)
            valores = [
                medico.medico_nombre,
                str(medico.total_citas),
                self._fmt_min(medico.espera_media_min),
                self._fmt_min(medico.duracion_media_consulta_min),
                self._fmt_min(medico.retraso_media_min),
            ]
            for col, valor in enumerate(valores):
                self.tabla_medicos.setItem(fila, col, QTableWidgetItem(valor))

    def _render_tabla_vigilancia(self, citas: tuple[CitaVigilarDTO, ...]) -> None:
        self.tabla_vigilancia.setRowCount(0)
        self.lbl_sin_vigilancia.setVisible(not citas)
        self.tabla_vigilancia.setVisible(bool(citas))
        for cita in citas:
            fila = self.tabla_vigilancia.rowCount()
            self.tabla_vigilancia.insertRow(fila)
            self.tabla_vigilancia.setItem(fila, 0, QTableWidgetItem(cita.hora))
            self.tabla_vigilancia.setItem(fila, 1, QTableWidgetItem(cita.paciente))
            self.tabla_vigilancia.setItem(fila, 2, QTableWidgetItem(cita.medico))
            self.tabla_vigilancia.setItem(fila, 3, QTableWidgetItem(self._texto_senales(cita)))
            boton = QPushButton(self._i18n.t("dashboard_gestion.citas_vigilar.btn.abrir"))
            boton.clicked.connect(lambda _=False, cita_id=cita.cita_id: self._abrir_cita_desde_gestion(cita_id))
            self.tabla_vigilancia.setCellWidget(fila, 4, boton)

    def _texto_senales(self, cita: CitaVigilarDTO) -> str:
        claves = []
        if cita.no_show_alto:
            claves.append(self._i18n.t("dashboard_gestion.citas_vigilar.senal.no_vino"))
        if cita.duracion_alta:
            claves.append(self._i18n.t("dashboard_gestion.citas_vigilar.senal.duracion"))
        if cita.espera_alta:
            claves.append(self._i18n.t("dashboard_gestion.citas_vigilar.senal.espera"))
        return " · ".join(claves)

    def _abrir_cita_desde_gestion(self, cita_id: int) -> None:
        intent = CitasNavigationIntentDTO(preset_rango="HOY", cita_id_destino=cita_id, preferir_pestana="LISTA")
        self._navegar_a("citas", intent=intent)

    def _navegar_a(self, key: str, intent: object | None = None) -> None:
        parent = self.parentWidget()
        while parent is not None and not hasattr(parent, "navigate"):
            parent = parent.parentWidget()
        if parent is not None:
            parent.navigate(key, intent=intent)

    def _mostrar_error(self, mensaje: str) -> None:
        self.lbl_estado.setText(mensaje)
        self.lbl_alertas.setText("")

    @staticmethod
    def _fmt_min(valor: float | None) -> str:
        return "-" if valor is None else f"{valor:.2f}"

    def _retranslate(self) -> None:
        self.btn_actualizar.setText(self._i18n.t("dashboard_gestion.btn.actualizar"))
        self.btn_reintentar.setText(self._i18n.t("dashboard_gestion.btn.reintentar"))
        self.lbl_prediccion_titulo.setText(self._i18n.t("dashboard_gestion.prediccion.titulo"))
        self._estado_titulos[0].setText(self._i18n.t("dashboard_gestion.prediccion.ausencias"))
        self._estado_titulos[1].setText(self._i18n.t("dashboard_gestion.prediccion.duracion"))
        self._estado_titulos[2].setText(self._i18n.t("dashboard_gestion.prediccion.espera"))
        self.btn_ir_ausencias.setText(self._i18n.t("dashboard_gestion.btn.ir_prediccion_ausencias"))
        self.btn_ir_estimaciones_duracion.setText(self._i18n.t("dashboard_gestion.btn.ir_estimaciones"))
        self.btn_ir_estimaciones_espera.setText(self._i18n.t("dashboard_gestion.btn.ir_estimaciones"))
        self._kpi_titles[0].setText(self._i18n.t("dashboard_gestion.kpi.volumen_diario"))
        self._kpi_titles[1].setText(self._i18n.t("dashboard_gestion.kpi.espera_media"))
        self._kpi_titles[2].setText(self._i18n.t("dashboard_gestion.kpi.duracion_media"))
        self._kpi_titles[3].setText(self._i18n.t("dashboard_gestion.kpi.retraso_medio"))
        self._llenar_presets()
        self.tabla_medicos.setHorizontalHeaderLabels(
            [
                self._i18n.t("dashboard_gestion.tabla.medico"),
                self._i18n.t("dashboard_gestion.tabla.citas"),
                self._i18n.t("dashboard_gestion.tabla.espera_media"),
                self._i18n.t("dashboard_gestion.tabla.duracion_media"),
                self._i18n.t("dashboard_gestion.tabla.retraso_medio"),
            ]
        )
        self.lbl_sin_vigilancia.setText(self._i18n.t("dashboard_gestion.citas_vigilar.vacio"))
        self.tabla_vigilancia.setHorizontalHeaderLabels(
            [
                self._i18n.t("dashboard_gestion.citas_vigilar.hora"),
                self._i18n.t("dashboard_gestion.citas_vigilar.paciente"),
                self._i18n.t("dashboard_gestion.citas_vigilar.medico"),
                self._i18n.t("dashboard_gestion.citas_vigilar.senales"),
                self._i18n.t("dashboard_gestion.citas_vigilar.accion"),
            ]
        )

    def _llenar_presets(self) -> None:
        actual = self.cmb_preset.currentData() or PRESET_7_DIAS
        self.cmb_preset.blockSignals(True)
        self.cmb_preset.clear()
        self.cmb_preset.addItem(self._i18n.t("dashboard_gestion.preset.hoy"), PRESET_HOY)
        self.cmb_preset.addItem(self._i18n.t("dashboard_gestion.preset.7_dias"), PRESET_7_DIAS)
        self.cmb_preset.addItem(self._i18n.t("dashboard_gestion.preset.30_dias"), PRESET_30_DIAS)
        self.cmb_preset.addItem(self._i18n.t("dashboard_gestion.preset.personalizado"), PRESET_PERSONALIZADO)
        idx = max(0, self.cmb_preset.findData(actual))
        self.cmb_preset.setCurrentIndex(idx)
        self.cmb_preset.blockSignals(False)
        self._on_cambio_preset()
