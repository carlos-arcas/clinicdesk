from __future__ import annotations
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    ColaTrabajoSeguroService,
    AnaliticaEjecutivaSegurosService,
    EconomiaValorSeguroService,
    AprendizajeComercialSegurosService,
    GestionComercialSeguroService,
    GestionCampaniasSeguroService,
    SolicitudCrearCampaniaDesdeSugerencia,
    SolicitudGestionItemCampaniaSeguro,
    RecomendadorProductoSeguroService,
    ScoringComercialSeguroService,
    SolicitudGestionItemColaSeguro,
    AgendaAlertasSeguroService,
)
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.domain.seguros import EstadoItemCampaniaSeguro, ResultadoItemCampaniaSeguro
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite
from clinicdesk.app.infrastructure.seguros.repositorio_campanias_sqlite import RepositorioCampaniasSeguroSqlite
from clinicdesk.app.infrastructure.sqlite_db import obtener_conexion
from clinicdesk.app.pages.seguros.cola_operaciones import construir_panel_operativo, construir_resumen_cartera
from clinicdesk.app.pages.seguros.operaciones_comerciales import (
    abrir_oportunidad_actual,
    analizar_actual,
    preparar_oferta_actual,
)
from clinicdesk.app.pages.seguros.analitica_ui_support import (
    construir_texto_campania_activa,
    construir_texto_cohortes,
    construir_texto_metricas_funnel,
    construir_texto_resumen_ejecutivo,
    construir_texto_aprendizaje,
    construir_texto_valor_economico,
    construir_texto_forecast,
    poblar_selector_campanias,
)
from clinicdesk.app.pages.seguros.page_ui_support import retranslate_page
from clinicdesk.app.pages.seguros.campanias_ui_support import (
    construir_texto_resultado_campania,
    poblar_selector_campanias_ejecutables,
    poblar_selector_items_campania,
)
from clinicdesk.app.pages.seguros.agenda_ui_support import (
    construir_texto_acciones_rapidas,
    construir_texto_alertas_activas,
    construir_texto_plan_semanal,
    construir_texto_tareas_vencidas,
)


class PageSeguros(QWidget):
    def __init__(self, i18n: I18nManager) -> None:
        super().__init__()
        self._i18n = i18n
        self._catalogo = CatalogoPlanesSeguro()
        self._use_case = AnalizarMigracionSeguroUseCase(self._catalogo)
        self._conexion = obtener_conexion()
        self._repositorio = RepositorioComercialSeguroSqlite(self._conexion)
        self._gestion = GestionComercialSeguroService(self._use_case, self._repositorio)
        self._scoring = ScoringComercialSeguroService(self._repositorio)
        self._recomendador = RecomendadorProductoSeguroService(self._catalogo, self._scoring)
        self._cola = ColaTrabajoSeguroService(self._repositorio, self._scoring, self._recomendador)
        self._economia_valor = EconomiaValorSeguroService(self._catalogo, self._scoring, self._recomendador)
        self._analitica = AnaliticaEjecutivaSegurosService(self._gestion, economia_valor=self._economia_valor)
        self._repo_campanias = RepositorioCampaniasSeguroSqlite(self._conexion)
        self._campanias = GestionCampaniasSeguroService(self._repo_campanias)
        self._aprendizaje = AprendizajeComercialSegurosService(self._gestion, self._campanias)
        self._agenda = AgendaAlertasSeguroService(self._cola, self._analitica, self._campanias)
        self._id_oportunidad_activa: str | None = None
        self._build_ui()
        self._popular_planes()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.box_filtros = QGroupBox()
        filtros = QFormLayout(self.box_filtros)
        self.cmb_origen = QComboBox()
        self.cmb_destino = QComboBox()
        self.cmb_impagos = QComboBox()
        filtros.addRow(QLabel(), self.cmb_origen)
        filtros.addRow(QLabel(), self.cmb_destino)
        filtros.addRow(QLabel(), self.cmb_impagos)

        acciones = QHBoxLayout()
        self.btn_analizar = QPushButton()
        self.btn_analizar.clicked.connect(self._analizar)
        self.btn_abrir_oportunidad = QPushButton()
        self.btn_abrir_oportunidad.clicked.connect(self._abrir_oportunidad)
        self.btn_preparar_oferta = QPushButton()
        self.btn_preparar_oferta.clicked.connect(self._preparar_oferta)
        acciones.addWidget(self.btn_analizar)
        acciones.addWidget(self.btn_abrir_oportunidad)
        acciones.addWidget(self.btn_preparar_oferta)
        acciones.addStretch(1)

        self.lbl_resumen = QLabel("-")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_detalle = QLabel("-")
        self.lbl_detalle.setWordWrap(True)
        self.lbl_estado_comercial = QLabel("-")
        self.lbl_estado_comercial.setWordWrap(True)

        self.box_seguimiento = QGroupBox()
        seguimiento_form = QFormLayout(self.box_seguimiento)
        self.input_accion = QLineEdit()
        self.input_nota = QLineEdit()
        self.input_siguiente = QLineEdit()
        self.cmb_estado_seguimiento = QComboBox()
        self.btn_registrar_seguimiento = QPushButton()
        self.btn_registrar_seguimiento.clicked.connect(self._registrar_seguimiento)
        self.cmb_cierre = QComboBox()
        self.btn_cerrar = QPushButton()
        self.btn_cerrar.clicked.connect(self._cerrar_oportunidad)
        seguimiento_form.addRow(QLabel(), self.input_accion)
        seguimiento_form.addRow(QLabel(), self.input_nota)
        seguimiento_form.addRow(QLabel(), self.input_siguiente)
        seguimiento_form.addRow(QLabel(), self.cmb_estado_seguimiento)
        seguimiento_form.addRow(self.btn_registrar_seguimiento)
        seguimiento_form.addRow(QLabel(), self.cmb_cierre)
        seguimiento_form.addRow(self.btn_cerrar)

        self.lbl_renovaciones = QLabel("-")
        self.lbl_renovaciones.setWordWrap(True)
        self.btn_refrescar_cartera = QPushButton()
        self.btn_refrescar_cartera.clicked.connect(self._refrescar_cartera)
        self.lbl_cartera = QLabel("-")
        self.lbl_cartera.setWordWrap(True)
        self.lbl_recomendacion = QLabel("-")
        self.lbl_recomendacion.setWordWrap(True)

        self.box_cola = QGroupBox()
        cola_form = QFormLayout(self.box_cola)
        self.cmb_filtro_cola = QComboBox()
        self.cmb_accion_cola = QComboBox()
        self.input_nota_cola = QLineEdit()
        self.input_siguiente_cola = QLineEdit()
        self.btn_registrar_accion_cola = QPushButton()
        self.btn_registrar_accion_cola.clicked.connect(self._registrar_accion_cola)
        cola_form.addRow(QLabel(), self.cmb_filtro_cola)
        cola_form.addRow(QLabel(), self.cmb_accion_cola)
        cola_form.addRow(QLabel(), self.input_nota_cola)
        cola_form.addRow(QLabel(), self.input_siguiente_cola)
        cola_form.addRow(self.btn_registrar_accion_cola)
        self.lbl_cola_operativa = QLabel("-")
        self.lbl_cola_operativa.setWordWrap(True)
        self.lbl_historial_operativo = QLabel("-")
        self.lbl_historial_operativo.setWordWrap(True)

        self.box_agenda = QGroupBox()
        panel_agenda = QFormLayout(self.box_agenda)
        self.lbl_alertas_activas = QLabel("-")
        self.lbl_alertas_activas.setWordWrap(True)
        self.lbl_plan_semanal = QLabel("-")
        self.lbl_plan_semanal.setWordWrap(True)
        self.lbl_tareas_vencidas = QLabel("-")
        self.lbl_tareas_vencidas.setWordWrap(True)
        self.lbl_acciones_rapidas = QLabel("-")
        self.lbl_acciones_rapidas.setWordWrap(True)
        panel_agenda.addRow(QLabel(), self.lbl_alertas_activas)
        panel_agenda.addRow(QLabel(), self.lbl_plan_semanal)
        panel_agenda.addRow(QLabel(), self.lbl_tareas_vencidas)
        panel_agenda.addRow(QLabel(), self.lbl_acciones_rapidas)

        self.box_ejecutivo = QGroupBox()
        panel_ejecutivo = QFormLayout(self.box_ejecutivo)
        self.lbl_resumen_ejecutivo = QLabel("-")
        self.lbl_resumen_ejecutivo.setWordWrap(True)
        self.lbl_metricas_funnel = QLabel("-")
        self.lbl_metricas_funnel.setWordWrap(True)
        self.lbl_cohortes = QLabel("-")
        self.lbl_cohortes.setWordWrap(True)
        self.cmb_campanias = QComboBox()
        self.btn_aplicar_campania = QPushButton()
        self.btn_aplicar_campania.clicked.connect(self._aplicar_campania)
        self.lbl_campania = QLabel("-")
        self.lbl_campania.setWordWrap(True)
        self.lbl_aprendizaje = QLabel("-")
        self.lbl_aprendizaje.setWordWrap(True)
        self.lbl_valor_economico = QLabel("-")
        self.lbl_valor_economico.setWordWrap(True)
        self.lbl_forecast = QLabel("-")
        self.lbl_forecast.setWordWrap(True)
        panel_ejecutivo.addRow(QLabel(), self.lbl_resumen_ejecutivo)
        panel_ejecutivo.addRow(QLabel(), self.lbl_metricas_funnel)
        panel_ejecutivo.addRow(QLabel(), self.lbl_cohortes)
        panel_ejecutivo.addRow(QLabel(), self.cmb_campanias)
        panel_ejecutivo.addRow(self.btn_aplicar_campania)
        panel_ejecutivo.addRow(QLabel(), self.lbl_campania)
        panel_ejecutivo.addRow(QLabel(), self.lbl_aprendizaje)
        panel_ejecutivo.addRow(QLabel(), self.lbl_valor_economico)
        panel_ejecutivo.addRow(QLabel(), self.lbl_forecast)

        self.btn_crear_campania = QPushButton()
        self.btn_crear_campania.clicked.connect(self._crear_campania_desde_sugerencia)
        panel_ejecutivo.addRow(self.btn_crear_campania)

        self.box_campanias = QGroupBox()
        panel_campanias = QFormLayout(self.box_campanias)
        self.cmb_campanias_ejecutables = QComboBox()
        self.cmb_items_campania = QComboBox()
        self.cmb_estado_item_campania = QComboBox()
        self.cmb_resultado_item_campania = QComboBox()
        self.input_accion_item_campania = QLineEdit()
        self.input_nota_item_campania = QLineEdit()
        self.btn_registrar_item_campania = QPushButton()
        self.btn_registrar_item_campania.clicked.connect(self._registrar_item_campania)
        self.lbl_resultado_campania = QLabel("-")
        self.lbl_resultado_campania.setWordWrap(True)
        panel_campanias.addRow(QLabel(), self.cmb_campanias_ejecutables)
        panel_campanias.addRow(QLabel(), self.cmb_items_campania)
        panel_campanias.addRow(QLabel(), self.cmb_estado_item_campania)
        panel_campanias.addRow(QLabel(), self.cmb_resultado_item_campania)
        panel_campanias.addRow(QLabel(), self.input_accion_item_campania)
        panel_campanias.addRow(QLabel(), self.input_nota_item_campania)
        panel_campanias.addRow(self.btn_registrar_item_campania)
        panel_campanias.addRow(QLabel(), self.lbl_resultado_campania)

        layout.addWidget(self.box_filtros)
        layout.addLayout(acciones)
        layout.addWidget(self.lbl_resumen)
        layout.addWidget(self.lbl_detalle)
        layout.addWidget(self.lbl_estado_comercial)
        layout.addWidget(self.box_seguimiento)
        layout.addWidget(self.lbl_renovaciones)
        layout.addWidget(self.btn_refrescar_cartera)
        layout.addWidget(self.lbl_cartera)
        layout.addWidget(self.lbl_recomendacion)
        layout.addWidget(self.box_cola)
        layout.addWidget(self.lbl_cola_operativa)
        layout.addWidget(self.lbl_historial_operativo)
        layout.addWidget(self.box_agenda)
        layout.addWidget(self.box_ejecutivo)
        layout.addWidget(self.box_campanias)
        layout.addStretch(1)

    def _popular_planes(self) -> None:
        for plan in self._catalogo.listar_planes_origen():
            self.cmb_origen.addItem(plan.nombre, plan.id_plan)
        for plan in self._catalogo.listar_planes_clinica():
            self.cmb_destino.addItem(plan.nombre, plan.id_plan)

    def _retranslate(self) -> None:
        retranslate_page(self)

    def _analizar(self) -> None:
        analizar_actual(self)

    def _abrir_oportunidad(self) -> None:
        abrir_oportunidad_actual(self)

    def _preparar_oferta(self) -> None:
        preparar_oferta_actual(self)

    def _registrar_seguimiento(self) -> None:
        if not self._id_oportunidad_activa:
            return
        oportunidad = self._gestion.registrar_seguimiento(
            self._id_oportunidad_activa,
            self.cmb_estado_seguimiento.currentData(),
            self.input_accion.text().strip() or "seguimiento",
            self.input_nota.text().strip() or "-",
            self.input_siguiente.text().strip() or "-",
        )
        self.lbl_estado_comercial.setText(
            self._i18n.t("seguros.comercial.estado").format(
                estado=oportunidad.estado_actual.value,
                motor=oportunidad.clasificacion_motor,
                fit=oportunidad.evaluacion_fit.encaje_plan.value if oportunidad.evaluacion_fit else "-",
            )
        )

    def _cerrar_oportunidad(self) -> None:
        if not self._id_oportunidad_activa:
            return
        oportunidad = self._gestion.cerrar_oportunidad(self._id_oportunidad_activa, self.cmb_cierre.currentData())
        renovaciones = self._gestion.listar_renovaciones_pendientes()
        self.lbl_estado_comercial.setText(
            self._i18n.t("seguros.comercial.cierre").format(
                estado=oportunidad.estado_actual.value,
                resultado=oportunidad.resultado_comercial.value if oportunidad.resultado_comercial else "-",
            )
        )
        self.lbl_renovaciones.setText(
            self._i18n.t("seguros.comercial.renovaciones_pendientes").format(cantidad=len(renovaciones))
        )
        self._refrescar_cartera()

    def _refrescar_cartera(self) -> None:
        resumen, caliente, abiertas = construir_resumen_cartera(self._i18n, self._gestion, self._scoring)
        self.lbl_cartera.setText(resumen)
        oportunidad_caliente = next((item for item in abiertas if item.id_oportunidad == caliente), None)
        if oportunidad_caliente:
            diagnostico = self._recomendador.evaluar_oportunidad(oportunidad_caliente)
            self.lbl_recomendacion.setText(
                self._i18n.t("seguros.recomendacion.resumen").format(
                    plan=diagnostico.recomendacion_plan.plan_recomendado_id or "-",
                    riesgo=diagnostico.riesgo_renovacion.semaforo.value,
                    argumento=diagnostico.argumento_comercial.angulo_principal,
                    accion=diagnostico.accion_retencion.accion_sugerida,
                    cautela=diagnostico.recomendacion_plan.cautela,
                )
            )
        else:
            self.lbl_recomendacion.setText(self._i18n.t("seguros.recomendacion.sin_dato"))
        cola_txt, historial_txt, activa = construir_panel_operativo(
            self._i18n,
            self._repositorio,
            self._cola,
            self._id_oportunidad_activa,
            self.cmb_filtro_cola.currentData(),
        )
        self.lbl_cola_operativa.setText(cola_txt)
        self.lbl_historial_operativo.setText(historial_txt)
        self._id_oportunidad_activa = activa
        plan = self._agenda.construir_plan_semanal()
        self.lbl_alertas_activas.setText(construir_texto_alertas_activas(self._i18n, plan))
        self.lbl_plan_semanal.setText(construir_texto_plan_semanal(self._i18n, plan))
        self.lbl_tareas_vencidas.setText(construir_texto_tareas_vencidas(self._i18n, plan))
        self.lbl_acciones_rapidas.setText(construir_texto_acciones_rapidas(self._i18n, plan))
        resumen_ejecutivo = self._analitica.construir_resumen()
        self.lbl_resumen_ejecutivo.setText(construir_texto_resumen_ejecutivo(self._i18n, resumen_ejecutivo))
        self.lbl_metricas_funnel.setText(construir_texto_metricas_funnel(self._i18n, resumen_ejecutivo))
        self.lbl_cohortes.setText(construir_texto_cohortes(self._i18n, resumen_ejecutivo))
        panel_aprendizaje = self._aprendizaje.construir_panel()
        self.lbl_aprendizaje.setText(construir_texto_aprendizaje(self._i18n, panel_aprendizaje))
        self.lbl_valor_economico.setText(construir_texto_valor_economico(self._i18n, resumen_ejecutivo))
        self.lbl_forecast.setText(construir_texto_forecast(self._i18n, resumen_ejecutivo))
        poblar_selector_campanias(self._i18n, self.cmb_campanias, resumen_ejecutivo)
        self._actualizar_detalle_campania(resumen_ejecutivo)
        self._refrescar_campanias_ejecutables()

    def _actualizar_detalle_campania(self, resumen_ejecutivo) -> None:
        id_campania = self.cmb_campanias.currentData()
        if not id_campania and resumen_ejecutivo.campanias:
            id_campania = resumen_ejecutivo.campanias[0].id_campania
        self.lbl_campania.setText(
            construir_texto_campania_activa(self._i18n, resumen_ejecutivo, str(id_campania or ""))
        )

    def _aplicar_campania(self) -> None:
        id_campania = self.cmb_campanias.currentData()
        if not id_campania:
            return
        ids = self._analitica.ids_oportunidad_por_campania(str(id_campania))
        if ids:
            self._id_oportunidad_activa = ids[0]
        self._refrescar_cartera()

    def _registrar_accion_cola(self) -> None:
        if not self._id_oportunidad_activa:
            return
        self._cola.registrar_gestion(
            SolicitudGestionItemColaSeguro(
                id_oportunidad=self._id_oportunidad_activa,
                accion=self.cmb_accion_cola.currentData(),
                nota_corta=self.input_nota_cola.text().strip(),
                siguiente_paso=self.input_siguiente_cola.text().strip(),
            )
        )
        self._refrescar_cartera()

    def _crear_campania_desde_sugerencia(self) -> None:
        id_campania = self.cmb_campanias.currentData()
        if not id_campania:
            return
        resumen = self._analitica.construir_resumen()
        sugerencia = next((c for c in resumen.campanias if c.id_campania == id_campania), None)
        if sugerencia is None:
            return
        nueva = f"exec-{id_campania}-{len(self._campanias.listar_campanias()) + 1}"
        self._campanias.crear_desde_sugerencia(
            SolicitudCrearCampaniaDesdeSugerencia(
                id_campania_nueva=nueva,
                objetivo_comercial=self._i18n.t("seguros.campania.objetivo_default"),
                sugerencia=sugerencia,
            )
        )
        self._refrescar_campanias_ejecutables()

    def _refrescar_campanias_ejecutables(self) -> None:
        campanias = self._campanias.listar_campanias()
        poblar_selector_campanias_ejecutables(self._i18n, self.cmb_campanias_ejecutables, campanias)
        self._poblar_estados_items_campania()
        id_campania = self.cmb_campanias_ejecutables.currentData()
        if not id_campania and campanias:
            id_campania = campanias[0].id_campania
        if not id_campania:
            self.lbl_resultado_campania.setText(self._i18n.t("seguros.campania.sin_dato"))
            return
        campania, items = self._campanias.obtener_detalle(str(id_campania))
        poblar_selector_items_campania(self._i18n, self.cmb_items_campania, items)
        self.lbl_resultado_campania.setText(construir_texto_resultado_campania(self._i18n, campania))

    def _registrar_item_campania(self) -> None:
        id_campania = self.cmb_campanias_ejecutables.currentData()
        id_item = self.cmb_items_campania.currentData()
        if not id_campania or not id_item:
            return
        self._campanias.registrar_resultado_item(
            SolicitudGestionItemCampaniaSeguro(
                id_campania=str(id_campania),
                id_item=str(id_item),
                estado_trabajo=self.cmb_estado_item_campania.currentData(),
                accion_tomada=self.input_accion_item_campania.text().strip(),
                resultado=self.cmb_resultado_item_campania.currentData(),
                nota_corta=self.input_nota_item_campania.text().strip(),
            )
        )
        self._refrescar_campanias_ejecutables()

    def _poblar_estados_items_campania(self) -> None:
        self.cmb_estado_item_campania.clear()
        for estado in EstadoItemCampaniaSeguro:
            self.cmb_estado_item_campania.addItem(estado.value, estado)
        self.cmb_resultado_item_campania.clear()
        for resultado in ResultadoItemCampaniaSeguro:
            self.cmb_resultado_item_campania.addItem(resultado.value, resultado)
