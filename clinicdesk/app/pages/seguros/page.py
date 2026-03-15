from __future__ import annotations

from datetime import date
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
    FiltroCarteraEconomicaPolizaSeguro,
    GestionEconomicaPolizaSeguroService,
    SolicitudEmitirCuotaPolizaSeguro,
    SolicitudRegistrarImpagoSeguro,
    SolicitudRegistrarPagoCuotaSeguro,
    SolicitudRegistrarReactivacionPolizaSeguro,
    SolicitudRegistrarSuspensionPolizaSeguro,
    CierreSemanalSeguroService,
    FiltroCarteraPolizaSeguro,
    GestionPostventaPolizaSeguroService,
    SolicitudAltaPolizaDesdeConversion,
    SolicitudRegistrarIncidenciaPoliza,
)
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.domain.seguros import EstadoItemCampaniaSeguro, ResultadoItemCampaniaSeguro
from clinicdesk.app.domain.seguros.postventa import (
    BeneficiarioSeguro,
    EstadoAseguradoSeguro,
    TipoIncidenciaPolizaSeguro,
)
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite
from clinicdesk.app.infrastructure.seguros.repositorio_campanias_sqlite import RepositorioCampaniasSeguroSqlite
from clinicdesk.app.infrastructure.seguros.repositorio_poliza_sqlite import RepositorioPolizaSeguroSqlite
from clinicdesk.app.infrastructure.seguros.repositorio_economia_poliza_sqlite import (
    RepositorioEconomiaPolizaSeguroSqlite,
)
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
from clinicdesk.app.pages.seguros.postventa_ui_support import (
    construir_texto_cartera_economica,
    construir_texto_cartera_postventa,
    estado_pago_desde_selector,
)
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
    construir_texto_bloqueos,
    construir_texto_cierre_semanal,
    construir_texto_recomendacion_cierre,
)


class PageSeguros(QWidget):
    def __init__(self, i18n: I18nManager) -> None:
        super().__init__()
        self._i18n = i18n
        self._catalogo = CatalogoPlanesSeguro()
        self._use_case = AnalizarMigracionSeguroUseCase(self._catalogo)
        self._conexion = obtener_conexion()
        self._repositorio = RepositorioComercialSeguroSqlite(self._conexion)
        self._repositorio_poliza = RepositorioPolizaSeguroSqlite(self._conexion)
        self._gestion = GestionComercialSeguroService(self._use_case, self._repositorio)
        self._postventa = GestionPostventaPolizaSeguroService(self._repositorio_poliza, self._repositorio)
        self._repo_economia_poliza = RepositorioEconomiaPolizaSeguroSqlite(self._conexion)
        self._economia_poliza = GestionEconomicaPolizaSeguroService(self._repo_economia_poliza)
        self._scoring = ScoringComercialSeguroService(self._repositorio)
        self._recomendador = RecomendadorProductoSeguroService(self._catalogo, self._scoring)
        self._cola = ColaTrabajoSeguroService(self._repositorio, self._scoring, self._recomendador)
        self._economia_valor = EconomiaValorSeguroService(self._catalogo, self._scoring, self._recomendador)
        self._analitica = AnaliticaEjecutivaSegurosService(self._gestion, economia_valor=self._economia_valor)
        self._repo_campanias = RepositorioCampaniasSeguroSqlite(self._conexion)
        self._campanias = GestionCampaniasSeguroService(self._repo_campanias)
        self._aprendizaje = AprendizajeComercialSegurosService(self._gestion, self._campanias)
        self._agenda = AgendaAlertasSeguroService(self._cola, self._analitica, self._campanias)
        self._cierre_semanal = CierreSemanalSeguroService(
            self._agenda, self._cola, self._analitica, self._campanias, self._repositorio
        )
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
        self.lbl_cierre_semanal = QLabel("-")
        self.lbl_cierre_semanal.setWordWrap(True)
        self.lbl_bloqueos_recurrentes = QLabel("-")
        self.lbl_bloqueos_recurrentes.setWordWrap(True)
        self.lbl_recomendacion_cierre = QLabel("-")
        self.lbl_recomendacion_cierre.setWordWrap(True)
        panel_agenda.addRow(QLabel(), self.lbl_cierre_semanal)
        panel_agenda.addRow(QLabel(), self.lbl_bloqueos_recurrentes)
        panel_agenda.addRow(QLabel(), self.lbl_recomendacion_cierre)

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

        self.box_postventa = QGroupBox()
        panel_postventa = QFormLayout(self.box_postventa)
        self.input_nombre_titular = QLineEdit()
        self.input_doc_titular = QLineEdit()
        self.input_nombre_beneficiario = QLineEdit()
        self.cmb_tipo_incidencia = QComboBox()
        self.input_periodo_cuota = QLineEdit()
        self.input_importe_cuota = QLineEdit()
        self.cmb_estado_pago_filtro = QComboBox()
        self.btn_emitir_cuota = QPushButton()
        self.btn_emitir_cuota.clicked.connect(self._emitir_cuota_postventa)
        self.btn_registrar_pago_cuota = QPushButton()
        self.btn_registrar_pago_cuota.clicked.connect(self._registrar_pago_cuota_postventa)
        self.btn_registrar_impago = QPushButton()
        self.btn_registrar_impago.clicked.connect(self._registrar_impago_postventa)
        self.btn_suspender_poliza = QPushButton()
        self.btn_suspender_poliza.clicked.connect(self._suspender_poliza_postventa)
        self.btn_reactivar_poliza = QPushButton()
        self.btn_reactivar_poliza.clicked.connect(self._reactivar_poliza_postventa)
        self.btn_materializar_poliza = QPushButton()
        self.btn_materializar_poliza.clicked.connect(self._materializar_poliza)
        self.btn_registrar_incidencia_poliza = QPushButton()
        self.btn_registrar_incidencia_poliza.clicked.connect(self._registrar_incidencia_poliza)
        self.lbl_postventa = QLabel("-")
        self.lbl_postventa.setWordWrap(True)
        self.lbl_postventa_economia = QLabel("-")
        self.lbl_postventa_economia.setWordWrap(True)
        panel_postventa.addRow(QLabel(), self.input_nombre_titular)
        panel_postventa.addRow(QLabel(), self.input_doc_titular)
        panel_postventa.addRow(QLabel(), self.input_nombre_beneficiario)
        panel_postventa.addRow(QLabel(), self.cmb_tipo_incidencia)
        panel_postventa.addRow(QLabel(), self.input_periodo_cuota)
        panel_postventa.addRow(QLabel(), self.input_importe_cuota)
        panel_postventa.addRow(QLabel(), self.cmb_estado_pago_filtro)
        panel_postventa.addRow(self.btn_materializar_poliza)
        panel_postventa.addRow(self.btn_registrar_incidencia_poliza)
        panel_postventa.addRow(self.btn_emitir_cuota)
        panel_postventa.addRow(self.btn_registrar_pago_cuota)
        panel_postventa.addRow(self.btn_registrar_impago)
        panel_postventa.addRow(self.btn_suspender_poliza)
        panel_postventa.addRow(self.btn_reactivar_poliza)
        panel_postventa.addRow(QLabel(), self.lbl_postventa)
        panel_postventa.addRow(QLabel(), self.lbl_postventa_economia)

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
        layout.addWidget(self.box_postventa)
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
        resumen_semana = self._cierre_semanal.construir_resumen_semana()
        self.lbl_cierre_semanal.setText(construir_texto_cierre_semanal(self._i18n, resumen_semana))
        self.lbl_bloqueos_recurrentes.setText(construir_texto_bloqueos(self._i18n, resumen_semana))
        self.lbl_recomendacion_cierre.setText(construir_texto_recomendacion_cierre(self._i18n, resumen_semana))
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
        self._refrescar_postventa()

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

    def _materializar_poliza(self) -> None:
        if not self._id_oportunidad_activa:
            return
        nombre_titular = self.input_nombre_titular.text().strip() or self._i18n.t("seguros.postventa.titular_default")
        documento = self.input_doc_titular.text().strip() or self._i18n.t("seguros.postventa.documento_default")
        nombre_beneficiario = self.input_nombre_beneficiario.text().strip()
        beneficiarios = ()
        if nombre_beneficiario:
            beneficiarios = (
                BeneficiarioSeguro(
                    id_beneficiario=f"ben-{self._id_oportunidad_activa}",
                    nombre=nombre_beneficiario,
                    parentesco="familiar",
                    estado=EstadoAseguradoSeguro.ACTIVO,
                ),
            )
        self._postventa.materializar_poliza_desde_conversion(
            SolicitudAltaPolizaDesdeConversion(
                id_oportunidad=self._id_oportunidad_activa,
                id_poliza=f"pol-{self._id_oportunidad_activa}",
                nombre_titular=nombre_titular,
                documento_titular=documento,
                fecha_inicio=date.today(),
                beneficiarios=beneficiarios,
            )
        )
        self._refrescar_postventa()

    def _registrar_incidencia_poliza(self) -> None:
        if not self._id_oportunidad_activa:
            return
        id_poliza = f"pol-{self._id_oportunidad_activa}"
        self._postventa.registrar_incidencia(
            SolicitudRegistrarIncidenciaPoliza(
                id_poliza=id_poliza,
                id_incidencia=f"inc-{id_poliza}",
                tipo=self.cmb_tipo_incidencia.currentData(),
                descripcion=self._i18n.t("seguros.postventa.incidencia_default"),
                fecha_apertura=date.today(),
            )
        )
        self._refrescar_postventa()


    def _emitir_cuota_postventa(self) -> None:
        if not self._id_oportunidad_activa:
            return
        id_poliza = f"pol-{self._id_oportunidad_activa}"
        periodo = self.input_periodo_cuota.text().strip() or date.today().strftime("%Y-%m")
        importe_txt = self.input_importe_cuota.text().strip()
        importe = float(importe_txt) if importe_txt else 120.0
        self._economia_poliza.emitir_cuota(
            SolicitudEmitirCuotaPolizaSeguro(
                id_cuota=f"cuota-{id_poliza}-{periodo}",
                id_poliza=id_poliza,
                periodo=periodo,
                fecha_emision=date.today(),
                fecha_vencimiento=date.today(),
                importe=importe,
            )
        )
        self._refrescar_postventa()

    def _registrar_pago_cuota_postventa(self) -> None:
        if not self._id_oportunidad_activa:
            return
        id_poliza = f"pol-{self._id_oportunidad_activa}"
        cuotas = self._repo_economia_poliza.listar_cuotas_poliza(id_poliza)
        if not cuotas:
            return
        self._economia_poliza.registrar_pago_cuota(
            SolicitudRegistrarPagoCuotaSeguro(id_cuota=cuotas[-1].id_cuota, fecha_pago=date.today())
        )
        self._refrescar_postventa()

    def _registrar_impago_postventa(self) -> None:
        if not self._id_oportunidad_activa:
            return
        id_poliza = f"pol-{self._id_oportunidad_activa}"
        cuotas = self._repo_economia_poliza.listar_cuotas_poliza(id_poliza)
        if not cuotas:
            return
        cuota = cuotas[-1]
        self._economia_poliza.registrar_impago(
            SolicitudRegistrarImpagoSeguro(
                id_evento=f"imp-{cuota.id_cuota}",
                id_poliza=id_poliza,
                id_cuota=cuota.id_cuota,
                fecha_evento=date.today(),
                motivo="Impago operativo registrado por backoffice",
            )
        )
        self._refrescar_postventa()

    def _suspender_poliza_postventa(self) -> None:
        if not self._id_oportunidad_activa:
            return
        id_poliza = f"pol-{self._id_oportunidad_activa}"
        self._economia_poliza.registrar_suspension(
            SolicitudRegistrarSuspensionPolizaSeguro(
                id_evento=f"sus-{id_poliza}",
                id_poliza=id_poliza,
                fecha_evento=date.today(),
                motivo="Suspension operativa por riesgo economico alto",
            )
        )
        self._refrescar_postventa()

    def _reactivar_poliza_postventa(self) -> None:
        if not self._id_oportunidad_activa:
            return
        id_poliza = f"pol-{self._id_oportunidad_activa}"
        self._economia_poliza.registrar_reactivacion(
            SolicitudRegistrarReactivacionPolizaSeguro(
                id_evento=f"rea-{id_poliza}",
                id_poliza=id_poliza,
                fecha_evento=date.today(),
                motivo="Reactivacion por regularizacion economica",
            )
        )
        self._refrescar_postventa()

    def _refrescar_postventa(self) -> None:
        polizas = self._postventa.listar_cartera(FiltroCarteraPolizaSeguro())
        self.lbl_postventa.setText(construir_texto_cartera_postventa(self._i18n, polizas))
        estado_pago = estado_pago_desde_selector(self.cmb_estado_pago_filtro.currentData())
        cartera = self._economia_poliza.listar_cartera_economica(
            FiltroCarteraEconomicaPolizaSeguro(estado_pago=estado_pago) if estado_pago else None
        )
        self.lbl_postventa_economia.setText(construir_texto_cartera_economica(self._i18n, cartera))

    def _poblar_estados_items_campania(self) -> None:
        self.cmb_estado_item_campania.clear()
        for estado in EstadoItemCampaniaSeguro:
            self.cmb_estado_item_campania.addItem(estado.value, estado)
        self.cmb_resultado_item_campania.clear()
        for resultado in ResultadoItemCampaniaSeguro:
            self.cmb_resultado_item_campania.addItem(resultado.value, resultado)
        self.cmb_tipo_incidencia.clear()
        for tipo in TipoIncidenciaPolizaSeguro:
            self.cmb_tipo_incidencia.addItem(tipo.value, tipo)
