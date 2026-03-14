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
    FiltroCarteraSeguro,
    GestionComercialSeguroService,
    SolicitudAnalisisMigracionSeguro,
    SolicitudNuevaOportunidadSeguro,
)
from clinicdesk.app.domain.seguros import (
    EstadoOportunidadSeguro,
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenClienteSeguro,
    ResultadoComercialSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite
from clinicdesk.app.infrastructure.sqlite_db import obtener_conexion


class PageSeguros(QWidget):
    def __init__(self, i18n: I18nManager) -> None:
        super().__init__()
        self._i18n = i18n
        self._catalogo = CatalogoPlanesSeguro()
        self._use_case = AnalizarMigracionSeguroUseCase(self._catalogo)
        self._conexion = obtener_conexion()
        self._gestion = GestionComercialSeguroService(self._use_case, RepositorioComercialSeguroSqlite(self._conexion))
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

        layout.addWidget(self.box_filtros)
        layout.addLayout(acciones)
        layout.addWidget(self.lbl_resumen)
        layout.addWidget(self.lbl_detalle)
        layout.addWidget(self.lbl_estado_comercial)
        layout.addWidget(self.box_seguimiento)
        layout.addWidget(self.lbl_renovaciones)
        layout.addWidget(self.btn_refrescar_cartera)
        layout.addWidget(self.lbl_cartera)
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
        self._popular_opciones_impagos()
        self._popular_seguimiento()

    def _analizar(self) -> None:
        solicitud = SolicitudAnalisisMigracionSeguro(
            plan_origen_id=str(self.cmb_origen.currentData()),
            plan_destino_id=str(self.cmb_destino.currentData()),
            edad=34,
            residencia_pais="ES",
            historial_impagos=self.cmb_impagos.currentData(),
            preexistencias_graves=False,
        )
        respuesta = self._use_case.execute(solicitud)
        simulacion = respuesta.simulacion
        self.lbl_resumen.setText(
            self._i18n.t("seguros.resultado.resumen").format(
                clasificacion=simulacion.clasificacion,
                texto=simulacion.resumen_ejecutivo,
            )
        )
        self.lbl_detalle.setText(
            self._i18n.t("seguros.resultado.detalle").format(
                mejoras=", ".join(simulacion.impactos_positivos) or "-",
                perdidas=", ".join(simulacion.impactos_negativos) or "-",
                advertencias=", ".join(simulacion.advertencias) or "-",
            )
        )

    def _abrir_oportunidad(self) -> None:
        id_oportunidad = f"opp-{self.cmb_origen.currentIndex()}-{self.cmb_destino.currentIndex()}"
        oportunidad = self._gestion.abrir_oportunidad(
            SolicitudNuevaOportunidadSeguro(
                id_oportunidad=id_oportunidad,
                id_candidato=f"cand-{id_oportunidad}",
                id_paciente="paciente-demo",
                segmento_cliente=SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
                origen_cliente=OrigenClienteSeguro.MOSTRADOR_CLINICA,
                necesidad_principal=NecesidadPrincipalSeguro.AHORRO_COSTE,
                motivaciones=(MotivacionCompraSeguro.MEJOR_RELACION_CALIDAD_PRECIO,),
                objecion_principal=ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
                sensibilidad_precio=SensibilidadPrecioSeguro.MEDIA,
                friccion_migracion=FriccionMigracionSeguro.MEDIA,
                plan_origen_id=str(self.cmb_origen.currentData()),
                plan_destino_id=str(self.cmb_destino.currentData()),
            )
        )
        self._id_oportunidad_activa = oportunidad.id_oportunidad
        self.lbl_estado_comercial.setText(
            self._i18n.t("seguros.comercial.estado").format(
                estado=oportunidad.estado_actual.value,
                motor=oportunidad.clasificacion_motor,
                fit=oportunidad.evaluacion_fit.encaje_plan.value if oportunidad.evaluacion_fit else "-",
            )
        )

    def _preparar_oferta(self) -> None:
        if not self._id_oportunidad_activa:
            return
        oferta = self._gestion.preparar_oferta(self._id_oportunidad_activa, ("nota_operativa",))
        self.lbl_detalle.setText(
            self._i18n.t("seguros.comercial.oferta").format(
                plan=oferta.plan_propuesto_id,
                clasificacion=oferta.clasificacion_migracion,
                valor=oferta.resumen_valor,
            )
        )

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
        abiertas = self._gestion.listar_cartera()
        convertidas = self._gestion.listar_oportunidades_por_estado(EstadoOportunidadSeguro.PENDIENTE_RENOVACION)
        seguimiento_reciente = self._gestion.listar_seguimiento_reciente(3)
        pendientes = self._gestion.listar_cartera(FiltroCarteraSeguro(solo_renovacion_pendiente=True))
        ultimo = seguimiento_reciente[0].accion_comercial if seguimiento_reciente else "-"
        self.lbl_cartera.setText(
            self._i18n.t("seguros.cartera.resumen").format(
                total=len(abiertas),
                pendientes=len(pendientes),
                convertidas=len(convertidas),
                ultimo=ultimo,
            )
        )
