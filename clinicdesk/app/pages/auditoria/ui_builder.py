from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QVBoxLayout, QWidget

from clinicdesk.app.pages.auditoria.contratos_ui import AuditoriaUIRefs
from clinicdesk.app.pages.auditoria.filtros_ui import columnas_tabla, opciones_accion, opciones_entidad, opciones_rango


def build_auditoria_ui(page: QWidget, traducir) -> AuditoriaUIRefs:
    root = QVBoxLayout(page)
    refs = _build_refs()
    root.addLayout(_build_resumen(refs, traducir))
    root.addLayout(_build_filtros(refs, traducir))
    refs.tabla.setHorizontalHeaderLabels([traducir(k) for k in columnas_tabla()])
    root.addWidget(refs.tabla)
    root.addLayout(_build_pie(refs))
    _cargar_combos(refs, traducir)
    return refs


def _build_refs() -> AuditoriaUIRefs:
    return AuditoriaUIRefs(
        lbl_accesos_hoy=QLabel("0"),
        lbl_accesos_7_dias=QLabel("0"),
        lbl_top_acciones=QLabel("-"),
        combo_rango=QComboBox(),
        combo_accion=QComboBox(),
        combo_entidad=QComboBox(),
        input_usuario=QLineEdit(),
        input_desde=QLineEdit(),
        input_hasta=QLineEdit(),
        btn_buscar=QPushButton(),
        btn_limpiar=QPushButton(),
        tabla=QTableWidget(0, 6),
        lbl_estado=QLabel(),
        btn_reintentar=QPushButton(),
        btn_exportar=QPushButton(),
        btn_cargar_mas=QPushButton(),
    )


def _build_resumen(refs: AuditoriaUIRefs, traducir) -> QGridLayout:
    grid = QGridLayout()
    grid.addWidget(QLabel(traducir("auditoria.resumen.accesos_hoy")), 0, 0)
    grid.addWidget(refs.lbl_accesos_hoy, 0, 1)
    grid.addWidget(QLabel(traducir("auditoria.resumen.accesos_7_dias")), 0, 2)
    grid.addWidget(refs.lbl_accesos_7_dias, 0, 3)
    grid.addWidget(QLabel(traducir("auditoria.resumen.top_acciones")), 1, 0)
    grid.addWidget(refs.lbl_top_acciones, 1, 1, 1, 3)
    return grid


def _build_filtros(refs: AuditoriaUIRefs, traducir) -> QHBoxLayout:
    filtros = QHBoxLayout()
    for key, widget in (
        ("auditoria.filtro.rango", refs.combo_rango),
        ("auditoria.filtro.usuario", refs.input_usuario),
        ("auditoria.filtro.accion", refs.combo_accion),
        ("auditoria.filtro.entidad", refs.combo_entidad),
        ("auditoria.filtro.desde", refs.input_desde),
        ("auditoria.filtro.hasta", refs.input_hasta),
    ):
        filtros.addWidget(QLabel(traducir(key)))
        filtros.addWidget(widget)
    filtros.addWidget(refs.btn_buscar)
    filtros.addWidget(refs.btn_limpiar)
    return filtros


def _build_pie(refs: AuditoriaUIRefs) -> QHBoxLayout:
    pie = QHBoxLayout()
    pie.addWidget(refs.lbl_estado)
    pie.addWidget(refs.btn_reintentar)
    pie.addStretch(1)
    pie.addWidget(refs.btn_exportar)
    pie.addWidget(refs.btn_cargar_mas)
    return pie


def _cargar_combos(refs: AuditoriaUIRefs, traducir) -> None:
    for combo, opciones in (
        (refs.combo_rango, opciones_rango(traducir)),
        (refs.combo_accion, opciones_accion(traducir)),
        (refs.combo_entidad, opciones_entidad(traducir)),
    ):
        combo.clear()
        for item in opciones:
            combo.addItem(item.texto, item.valor)
