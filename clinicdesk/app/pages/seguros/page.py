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
    GestionComercialSeguroService,
    RecomendadorProductoSeguroService,
    ScoringComercialSeguroService,
    SolicitudGestionItemColaSeguro,
)
from clinicdesk.app.domain.seguros import EstadoOportunidadSeguro, ResultadoComercialSeguro
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite
from clinicdesk.app.infrastructure.sqlite_db import obtener_conexion
from clinicdesk.app.pages.seguros.cola_operaciones import construir_panel_operativo, construir_resumen_cartera
from clinicdesk.app.pages.seguros.operaciones_comerciales import (
    abrir_oportunidad_actual,
    analizar_actual,
    preparar_oferta_actual,
)
from clinicdesk.app.pages.seguros.cola_ui_support import popular_filtros_y_acciones


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
        self._id_oportunidad_activa: str | None = None
        self._build_ui()
        self._popular_planes()
        self._popular_opciones_impagos()
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
        layout.addStretch(1)

    def _popular_planes(self) -> None:
        for plan in self._catalogo.listar_planes_origen():
            self.cmb_origen.addItem(plan.nombre, plan.id_plan)
        for plan in self._catalogo.listar_planes_clinica():
            self.cmb_destino.addItem(plan.nombre, plan.id_plan)

    def _popular_opciones_impagos(self) -> None:
        self.cmb_impagos.clear()
        self.cmb_impagos.addItem(self._i18n.t("seguros.filtros.impagos.sin_dato"), None)
        self.cmb_impagos.addItem(self._i18n.t("comun.no"), False)
        self.cmb_impagos.addItem(self._i18n.t("comun.si"), True)

    def _popular_seguimiento(self) -> None:
        self.cmb_estado_seguimiento.clear()
        for estado in (EstadoOportunidadSeguro.OFERTA_ENVIADA, EstadoOportunidadSeguro.EN_SEGUIMIENTO):
            self.cmb_estado_seguimiento.addItem(estado.value, estado)
        self.cmb_cierre.clear()
        for resultado in ResultadoComercialSeguro:
            self.cmb_cierre.addItem(resultado.value, resultado)

    def _retranslate(self) -> None:
        self.box_filtros.setTitle(self._i18n.t("seguros.filtros.titulo"))
        form = self.box_filtros.layout()
        form.labelForField(self.cmb_origen).setText(self._i18n.t("seguros.filtros.plan_origen"))
        form.labelForField(self.cmb_destino).setText(self._i18n.t("seguros.filtros.plan_destino"))
        form.labelForField(self.cmb_impagos).setText(self._i18n.t("seguros.filtros.impagos"))
        self.btn_analizar.setText(self._i18n.t("seguros.accion.analizar"))
        self.btn_abrir_oportunidad.setText(self._i18n.t("seguros.accion.abrir_oportunidad"))
        self.btn_preparar_oferta.setText(self._i18n.t("seguros.accion.preparar_oferta"))
        self.box_seguimiento.setTitle(self._i18n.t("seguros.seguimiento.titulo"))
        form_seg = self.box_seguimiento.layout()
        form_seg.labelForField(self.input_accion).setText(self._i18n.t("seguros.seguimiento.accion"))
        form_seg.labelForField(self.input_nota).setText(self._i18n.t("seguros.seguimiento.nota"))
        form_seg.labelForField(self.input_siguiente).setText(self._i18n.t("seguros.seguimiento.siguiente_paso"))
        form_seg.labelForField(self.cmb_estado_seguimiento).setText(self._i18n.t("seguros.seguimiento.estado"))
        form_seg.labelForField(self.cmb_cierre).setText(self._i18n.t("seguros.seguimiento.cierre"))
        self.btn_registrar_seguimiento.setText(self._i18n.t("seguros.accion.registrar_seguimiento"))
        self.btn_cerrar.setText(self._i18n.t("seguros.accion.cerrar_oportunidad"))
        self.btn_refrescar_cartera.setText(self._i18n.t("seguros.accion.refrescar_cartera"))
        self.box_cola.setTitle(self._i18n.t("seguros.cola.titulo"))
        form_cola = self.box_cola.layout()
        form_cola.labelForField(self.cmb_filtro_cola).setText(self._i18n.t("seguros.cola.filtro"))
        form_cola.labelForField(self.cmb_accion_cola).setText(self._i18n.t("seguros.cola.accion"))
        form_cola.labelForField(self.input_nota_cola).setText(self._i18n.t("seguros.cola.nota"))
        form_cola.labelForField(self.input_siguiente_cola).setText(self._i18n.t("seguros.cola.siguiente"))
        self.btn_registrar_accion_cola.setText(self._i18n.t("seguros.cola.registrar"))
        self._popular_opciones_impagos()
        self._popular_seguimiento()
        popular_filtros_y_acciones(self._i18n, self.cmb_filtro_cola, self.cmb_accion_cola)

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
