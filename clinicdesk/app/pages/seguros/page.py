from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    SolicitudAnalisisMigracionSeguro,
)
from clinicdesk.app.i18n import I18nManager


class PageSeguros(QWidget):
    def __init__(self, i18n: I18nManager) -> None:
        super().__init__()
        self._i18n = i18n
        self._catalogo = CatalogoPlanesSeguro()
        self._use_case = AnalizarMigracionSeguroUseCase(self._catalogo)
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
        acciones.addWidget(self.btn_analizar)
        acciones.addStretch(1)

        self.lbl_resumen = QLabel("-")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_detalle = QLabel("-")
        self.lbl_detalle.setWordWrap(True)

        layout.addWidget(self.box_filtros)
        layout.addLayout(acciones)
        layout.addWidget(self.lbl_resumen)
        layout.addWidget(self.lbl_detalle)
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

    def _retranslate(self) -> None:
        self.box_filtros.setTitle(self._i18n.t("seguros.filtros.titulo"))
        form = self.box_filtros.layout()
        form.labelForField(self.cmb_origen).setText(self._i18n.t("seguros.filtros.plan_origen"))
        form.labelForField(self.cmb_destino).setText(self._i18n.t("seguros.filtros.plan_destino"))
        form.labelForField(self.cmb_impagos).setText(self._i18n.t("seguros.filtros.impagos"))
        self.btn_analizar.setText(self._i18n.t("seguros.accion.analizar"))
        self._popular_opciones_impagos()

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
