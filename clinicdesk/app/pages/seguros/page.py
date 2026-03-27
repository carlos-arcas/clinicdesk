from __future__ import annotations

from clinicdesk.app.application.seguros import (
    AgendaAlertasSeguroService,
    AnalizarMigracionSeguroUseCase,
    AnaliticaEjecutivaSegurosService,
    AprendizajeComercialSegurosService,
    CierreSemanalSeguroService,
    ColaTrabajoSeguroService,
    EconomiaValorSeguroService,
    GestionCampaniasSeguroService,
    GestionComercialSeguroService,
    GestionEconomicaPolizaSeguroService,
    GestionPostventaPolizaSeguroService,
    RecomendadorProductoSeguroService,
    ScoringComercialSeguroService,
)
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.infrastructure.seguros.repositorio_campanias_sqlite import RepositorioCampaniasSeguroSqlite
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite
from clinicdesk.app.infrastructure.seguros.repositorio_economia_poliza_sqlite import (
    RepositorioEconomiaPolizaSeguroSqlite,
)
from clinicdesk.app.infrastructure.seguros.repositorio_poliza_sqlite import RepositorioPolizaSeguroSqlite
from clinicdesk.app.infrastructure.sqlite_db import obtener_conexion
from clinicdesk.app.pages.seguros.operaciones_comerciales import (
    abrir_oportunidad_actual,
    analizar_actual,
    preparar_oferta_actual,
)
from clinicdesk.app.pages.seguros.page_actions_comercial import (
    aplicar_campania,
    cerrar_oportunidad,
    crear_campania_desde_sugerencia,
    refrescar_campanias_ejecutables,
    refrescar_cartera,
    registrar_accion_cola,
    registrar_item_campania,
    registrar_seguimiento,
)
from clinicdesk.app.pages.seguros.page_actions_postventa import (
    emitir_cuota_postventa,
    materializar_poliza,
    poblar_tipos_incidencia,
    reactivar_poliza_postventa,
    refrescar_postventa,
    registrar_impago_postventa,
    registrar_incidencia_poliza,
    registrar_pago_cuota_postventa,
    suspender_poliza_postventa,
)
from clinicdesk.app.pages.seguros.page_ui_support import retranslate_page
from clinicdesk.app.pages.seguros.workspace_layout import construir_layout_workspace
from clinicdesk.app.pages.seguros.workspace_navegacion import (
    EstadoWorkspaceSeguros,
    construir_opciones_selector,
    indice_seccion,
    restaurar_seccion_preferida,
)
from PySide6.QtWidgets import QWidget


class PageSeguros(QWidget):
    def __init__(self, i18n: I18nManager) -> None:
        super().__init__()
        self._i18n = i18n
        self._estado_workspace = EstadoWorkspaceSeguros()
        self._inicializar_servicios()
        self._id_oportunidad_activa: str | None = None
        construir_layout_workspace(self)
        self._popular_planes()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()
        self._restaurar_navegacion_workspace()

    def _inicializar_servicios(self) -> None:
        from clinicdesk.app.application.seguros import CatalogoPlanesSeguro

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

    def _popular_planes(self) -> None:
        for plan in self._catalogo.listar_planes_origen():
            self.cmb_origen.addItem(plan.nombre, plan.id_plan)
        for plan in self._catalogo.listar_planes_clinica():
            self.cmb_destino.addItem(plan.nombre, plan.id_plan)

    def _retranslate(self) -> None:
        retranslate_page(self)
        opciones = construir_opciones_selector(self._i18n)
        self.selector_seccion.blockSignals(True)
        self.selector_seccion.clear()
        for texto, seccion in opciones:
            self.selector_seccion.addItem(texto, seccion)
        self.selector_seccion.blockSignals(False)
        self._restaurar_navegacion_workspace()
        self._refrescar_cartera()

    def _restaurar_navegacion_workspace(self) -> None:
        seccion = restaurar_seccion_preferida(self._estado_workspace)
        index = indice_seccion(seccion)
        self.selector_seccion.setCurrentIndex(index)
        self.workspace_secciones.setCurrentIndex(index)

    def _cambiar_seccion_workspace(self) -> None:
        seccion = self.selector_seccion.currentData()
        activa = self._estado_workspace.seleccionar(str(seccion or ""))
        self.workspace_secciones.setCurrentIndex(indice_seccion(activa))

    def _analizar(self) -> None:
        analizar_actual(self)

    def _abrir_oportunidad(self) -> None:
        abrir_oportunidad_actual(self)

    def _preparar_oferta(self) -> None:
        preparar_oferta_actual(self)

    def _registrar_seguimiento(self) -> None:
        registrar_seguimiento(self)

    def _cerrar_oportunidad(self) -> None:
        cerrar_oportunidad(self)

    def _refrescar_cartera(self) -> None:
        refrescar_cartera(self)

    def _aplicar_campania(self) -> None:
        aplicar_campania(self)

    def _registrar_accion_cola(self) -> None:
        registrar_accion_cola(self)

    def _crear_campania_desde_sugerencia(self) -> None:
        crear_campania_desde_sugerencia(self)

    def _refrescar_campanias_ejecutables(self) -> None:
        refrescar_campanias_ejecutables(self)

    def _registrar_item_campania(self) -> None:
        registrar_item_campania(self)

    def _materializar_poliza(self) -> None:
        materializar_poliza(self)

    def _registrar_incidencia_poliza(self) -> None:
        registrar_incidencia_poliza(self)

    def _emitir_cuota_postventa(self) -> None:
        emitir_cuota_postventa(self)

    def _registrar_pago_cuota_postventa(self) -> None:
        registrar_pago_cuota_postventa(self)

    def _registrar_impago_postventa(self) -> None:
        registrar_impago_postventa(self)

    def _suspender_poliza_postventa(self) -> None:
        suspender_poliza_postventa(self)

    def _reactivar_poliza_postventa(self) -> None:
        reactivar_poliza_postventa(self)

    def _refrescar_postventa(self) -> None:
        refrescar_postventa(self)

    def _poblar_estados_items_campania(self) -> None:
        from clinicdesk.app.pages.seguros.page_actions_comercial import poblar_estados_items_campania

        poblar_estados_items_campania(self)
        poblar_tipos_incidencia(self)
