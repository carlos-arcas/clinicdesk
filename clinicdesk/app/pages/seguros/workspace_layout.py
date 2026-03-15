from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.pages.seguros.workspace_navegacion import SECCIONES_WORKSPACE_SEGUROS


def construir_layout_workspace(page) -> None:
    layout = QVBoxLayout(page)
    page.selector_seccion = QComboBox()
    page.selector_seccion.currentIndexChanged.connect(page._cambiar_seccion_workspace)
    layout.addWidget(page.selector_seccion)
    page.workspace_secciones = QStackedWidget()
    layout.addWidget(page.workspace_secciones)

    _construir_bloques_preventa(page)
    _construir_bloques_cartera(page)
    _construir_bloques_campanias(page)
    _construir_bloques_analitica(page)
    _construir_bloques_agenda(page)
    _construir_bloques_postventa(page)
    _construir_bloques_economia(page)

    page._workspace_widgets = {
        "preventa": _componer_seccion(
            page, [page.box_filtros, page._acciones_preventa, page.lbl_resumen, page.lbl_detalle]
        ),
        "cartera": _componer_seccion(
            page,
            [
                page.lbl_estado_comercial,
                page.box_seguimiento,
                page.lbl_renovaciones,
                page.btn_refrescar_cartera,
                page.lbl_cartera,
                page.lbl_recomendacion,
                page.box_cola,
                page.lbl_cola_operativa,
                page.lbl_historial_operativo,
            ],
        ),
        "campanias": _componer_seccion(page, [page.box_campanias]),
        "analitica": _componer_seccion(page, [page.box_ejecutivo]),
        "agenda": _componer_seccion(page, [page.box_agenda]),
        "postventa": _componer_seccion(page, [page.box_postventa]),
        "economia": _componer_seccion(page, [page.box_estado_economia]),
    }
    for seccion in SECCIONES_WORKSPACE_SEGUROS:
        page.workspace_secciones.addWidget(page._workspace_widgets[seccion])


def _componer_seccion(page, elementos: list[QWidget | QHBoxLayout]) -> QWidget:
    contenedor = QWidget()
    layout = QVBoxLayout(contenedor)
    for elemento in elementos:
        if isinstance(elemento, QHBoxLayout):
            layout.addLayout(elemento)
        else:
            layout.addWidget(elemento)
    layout.addStretch(1)
    return contenedor


def _construir_bloques_preventa(page) -> None:
    page.box_filtros = QGroupBox()
    filtros = QFormLayout(page.box_filtros)
    page.cmb_origen = QComboBox()
    page.cmb_destino = QComboBox()
    page.cmb_impagos = QComboBox()
    filtros.addRow(QLabel(), page.cmb_origen)
    filtros.addRow(QLabel(), page.cmb_destino)
    filtros.addRow(QLabel(), page.cmb_impagos)

    acciones = QHBoxLayout()
    page.btn_analizar = QPushButton()
    page.btn_analizar.clicked.connect(page._analizar)
    page.btn_abrir_oportunidad = QPushButton()
    page.btn_abrir_oportunidad.clicked.connect(page._abrir_oportunidad)
    page.btn_preparar_oferta = QPushButton()
    page.btn_preparar_oferta.clicked.connect(page._preparar_oferta)
    acciones.addWidget(page.btn_analizar)
    acciones.addWidget(page.btn_abrir_oportunidad)
    acciones.addWidget(page.btn_preparar_oferta)
    acciones.addStretch(1)
    page._acciones_preventa = acciones

    page.lbl_resumen = QLabel("-")
    page.lbl_resumen.setWordWrap(True)
    page.lbl_detalle = QLabel("-")
    page.lbl_detalle.setWordWrap(True)


def _construir_bloques_cartera(page) -> None:
    page.lbl_estado_comercial = QLabel("-")
    page.lbl_estado_comercial.setWordWrap(True)
    page.box_seguimiento = QGroupBox()
    seguimiento_form = QFormLayout(page.box_seguimiento)
    page.input_accion = QLineEdit()
    page.input_nota = QLineEdit()
    page.input_siguiente = QLineEdit()
    page.cmb_estado_seguimiento = QComboBox()
    page.btn_registrar_seguimiento = QPushButton()
    page.btn_registrar_seguimiento.clicked.connect(page._registrar_seguimiento)
    page.cmb_cierre = QComboBox()
    page.btn_cerrar = QPushButton()
    page.btn_cerrar.clicked.connect(page._cerrar_oportunidad)
    seguimiento_form.addRow(QLabel(), page.input_accion)
    seguimiento_form.addRow(QLabel(), page.input_nota)
    seguimiento_form.addRow(QLabel(), page.input_siguiente)
    seguimiento_form.addRow(QLabel(), page.cmb_estado_seguimiento)
    seguimiento_form.addRow(page.btn_registrar_seguimiento)
    seguimiento_form.addRow(QLabel(), page.cmb_cierre)
    seguimiento_form.addRow(page.btn_cerrar)
    page.lbl_renovaciones = QLabel("-")
    page.lbl_renovaciones.setWordWrap(True)
    page.btn_refrescar_cartera = QPushButton()
    page.btn_refrescar_cartera.clicked.connect(page._refrescar_cartera)
    page.lbl_cartera = QLabel("-")
    page.lbl_cartera.setWordWrap(True)
    page.lbl_recomendacion = QLabel("-")
    page.lbl_recomendacion.setWordWrap(True)
    page.box_cola = QGroupBox()
    cola_form = QFormLayout(page.box_cola)
    page.cmb_filtro_cola = QComboBox()
    page.cmb_accion_cola = QComboBox()
    page.input_nota_cola = QLineEdit()
    page.input_siguiente_cola = QLineEdit()
    page.btn_registrar_accion_cola = QPushButton()
    page.btn_registrar_accion_cola.clicked.connect(page._registrar_accion_cola)
    cola_form.addRow(QLabel(), page.cmb_filtro_cola)
    cola_form.addRow(QLabel(), page.cmb_accion_cola)
    cola_form.addRow(QLabel(), page.input_nota_cola)
    cola_form.addRow(QLabel(), page.input_siguiente_cola)
    cola_form.addRow(page.btn_registrar_accion_cola)
    page.lbl_cola_operativa = QLabel("-")
    page.lbl_cola_operativa.setWordWrap(True)
    page.lbl_historial_operativo = QLabel("-")
    page.lbl_historial_operativo.setWordWrap(True)


def _construir_bloques_analitica(page) -> None:
    page.box_ejecutivo = QGroupBox()
    panel = QFormLayout(page.box_ejecutivo)
    page.lbl_resumen_ejecutivo = QLabel("-")
    page.lbl_metricas_funnel = QLabel("-")
    page.lbl_cohortes = QLabel("-")
    page.cmb_campanias = QComboBox()
    page.btn_aplicar_campania = QPushButton()
    page.btn_aplicar_campania.clicked.connect(page._aplicar_campania)
    page.lbl_campania = QLabel("-")
    page.lbl_aprendizaje = QLabel("-")
    page.lbl_valor_economico = QLabel("-")
    page.lbl_forecast = QLabel("-")
    for label in (
        page.lbl_resumen_ejecutivo,
        page.lbl_metricas_funnel,
        page.lbl_cohortes,
        page.lbl_campania,
        page.lbl_aprendizaje,
        page.lbl_valor_economico,
        page.lbl_forecast,
    ):
        label.setWordWrap(True)
    panel.addRow(QLabel(), page.lbl_resumen_ejecutivo)
    panel.addRow(QLabel(), page.lbl_metricas_funnel)
    panel.addRow(QLabel(), page.lbl_cohortes)
    panel.addRow(QLabel(), page.cmb_campanias)
    panel.addRow(page.btn_aplicar_campania)
    panel.addRow(QLabel(), page.lbl_campania)
    panel.addRow(QLabel(), page.lbl_aprendizaje)
    panel.addRow(QLabel(), page.lbl_valor_economico)
    panel.addRow(QLabel(), page.lbl_forecast)
    page.btn_crear_campania = QPushButton()
    page.btn_crear_campania.clicked.connect(page._crear_campania_desde_sugerencia)
    panel.addRow(page.btn_crear_campania)


def _construir_bloques_campanias(page) -> None:
    page.box_campanias = QGroupBox()
    panel = QFormLayout(page.box_campanias)
    page.cmb_campanias_ejecutables = QComboBox()
    page.cmb_items_campania = QComboBox()
    page.cmb_estado_item_campania = QComboBox()
    page.cmb_resultado_item_campania = QComboBox()
    page.input_accion_item_campania = QLineEdit()
    page.input_nota_item_campania = QLineEdit()
    page.btn_registrar_item_campania = QPushButton()
    page.btn_registrar_item_campania.clicked.connect(page._registrar_item_campania)
    page.lbl_resultado_campania = QLabel("-")
    page.lbl_resultado_campania.setWordWrap(True)
    panel.addRow(QLabel(), page.cmb_campanias_ejecutables)
    panel.addRow(QLabel(), page.cmb_items_campania)
    panel.addRow(QLabel(), page.cmb_estado_item_campania)
    panel.addRow(QLabel(), page.cmb_resultado_item_campania)
    panel.addRow(QLabel(), page.input_accion_item_campania)
    panel.addRow(QLabel(), page.input_nota_item_campania)
    panel.addRow(page.btn_registrar_item_campania)
    panel.addRow(QLabel(), page.lbl_resultado_campania)


def _construir_bloques_agenda(page) -> None:
    page.box_agenda = QGroupBox()
    panel = QFormLayout(page.box_agenda)
    page.lbl_alertas_activas = QLabel("-")
    page.lbl_plan_semanal = QLabel("-")
    page.lbl_tareas_vencidas = QLabel("-")
    page.lbl_acciones_rapidas = QLabel("-")
    page.lbl_cierre_semanal = QLabel("-")
    page.lbl_bloqueos_recurrentes = QLabel("-")
    page.lbl_recomendacion_cierre = QLabel("-")
    for label in (
        page.lbl_alertas_activas,
        page.lbl_plan_semanal,
        page.lbl_tareas_vencidas,
        page.lbl_acciones_rapidas,
        page.lbl_cierre_semanal,
        page.lbl_bloqueos_recurrentes,
        page.lbl_recomendacion_cierre,
    ):
        label.setWordWrap(True)
    panel.addRow(QLabel(), page.lbl_alertas_activas)
    panel.addRow(QLabel(), page.lbl_plan_semanal)
    panel.addRow(QLabel(), page.lbl_tareas_vencidas)
    panel.addRow(QLabel(), page.lbl_acciones_rapidas)
    panel.addRow(QLabel(), page.lbl_cierre_semanal)
    panel.addRow(QLabel(), page.lbl_bloqueos_recurrentes)
    panel.addRow(QLabel(), page.lbl_recomendacion_cierre)


def _construir_bloques_postventa(page) -> None:
    page.box_postventa = QGroupBox()
    panel = QFormLayout(page.box_postventa)
    page.input_nombre_titular = QLineEdit()
    page.input_doc_titular = QLineEdit()
    page.input_nombre_beneficiario = QLineEdit()
    page.cmb_tipo_incidencia = QComboBox()
    page.btn_materializar_poliza = QPushButton()
    page.btn_materializar_poliza.clicked.connect(page._materializar_poliza)
    page.btn_registrar_incidencia_poliza = QPushButton()
    page.btn_registrar_incidencia_poliza.clicked.connect(page._registrar_incidencia_poliza)
    page.lbl_postventa = QLabel("-")
    page.lbl_postventa.setWordWrap(True)
    panel.addRow(QLabel(), page.input_nombre_titular)
    panel.addRow(QLabel(), page.input_doc_titular)
    panel.addRow(QLabel(), page.input_nombre_beneficiario)
    panel.addRow(QLabel(), page.cmb_tipo_incidencia)
    panel.addRow(page.btn_materializar_poliza)
    panel.addRow(page.btn_registrar_incidencia_poliza)
    panel.addRow(QLabel(), page.lbl_postventa)


def _construir_bloques_economia(page) -> None:
    page.box_estado_economia = QGroupBox()
    panel = QFormLayout(page.box_estado_economia)
    page.input_periodo_cuota = QLineEdit()
    page.input_importe_cuota = QLineEdit()
    page.cmb_estado_pago_filtro = QComboBox()
    page.btn_emitir_cuota = QPushButton()
    page.btn_emitir_cuota.clicked.connect(page._emitir_cuota_postventa)
    page.btn_registrar_pago_cuota = QPushButton()
    page.btn_registrar_pago_cuota.clicked.connect(page._registrar_pago_cuota_postventa)
    page.btn_registrar_impago = QPushButton()
    page.btn_registrar_impago.clicked.connect(page._registrar_impago_postventa)
    page.btn_suspender_poliza = QPushButton()
    page.btn_suspender_poliza.clicked.connect(page._suspender_poliza_postventa)
    page.btn_reactivar_poliza = QPushButton()
    page.btn_reactivar_poliza.clicked.connect(page._reactivar_poliza_postventa)
    page.lbl_postventa_economia = QLabel("-")
    page.lbl_postventa_economia.setWordWrap(True)
    panel.addRow(QLabel(), page.input_periodo_cuota)
    panel.addRow(QLabel(), page.input_importe_cuota)
    panel.addRow(QLabel(), page.cmb_estado_pago_filtro)
    panel.addRow(page.btn_emitir_cuota)
    panel.addRow(page.btn_registrar_pago_cuota)
    panel.addRow(page.btn_registrar_impago)
    panel.addRow(page.btn_suspender_poliza)
    panel.addRow(page.btn_reactivar_poliza)
    panel.addRow(QLabel(), page.lbl_postventa_economia)
