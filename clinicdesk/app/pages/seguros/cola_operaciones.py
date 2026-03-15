from __future__ import annotations

from clinicdesk.app.application.seguros import (
    ColaTrabajoSeguroService,
    FiltroCarteraSeguro,
    GestionComercialSeguroService,
    ScoringComercialSeguroService,
)
from clinicdesk.app.domain.seguros import EstadoOportunidadSeguro
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.infrastructure.seguros.repositorio_comercial_sqlite import RepositorioComercialSeguroSqlite
from clinicdesk.app.pages.seguros.cola_ui_support import render_historial_gestion, render_items_cola


def construir_resumen_cartera(
    i18n: I18nManager,
    gestion: GestionComercialSeguroService,
    scoring: ScoringComercialSeguroService,
) -> tuple[str, str, tuple[object, ...]]:
    abiertas = gestion.listar_cartera()
    convertidas = gestion.listar_oportunidades_por_estado(EstadoOportunidadSeguro.PENDIENTE_RENOVACION)
    seguimiento_reciente = gestion.listar_seguimiento_reciente(3)
    pendientes = gestion.listar_cartera(FiltroCarteraSeguro(solo_renovacion_pendiente=True))
    ultimo = seguimiento_reciente[0].accion_comercial if seguimiento_reciente else "-"
    cartera = scoring.priorizar_cartera(abiertas)
    caliente = cartera.oportunidad_mas_caliente.id_oportunidad if cartera.oportunidad_mas_caliente else "-"
    vigilar = ", ".join(item.id_oportunidad for item in cartera.oportunidades_vigilar[:3]) or "-"
    no_prioritarias = ", ".join(item.id_oportunidad for item in cartera.oportunidades_no_prioritarias[:3]) or "-"
    resumen = i18n.t("seguros.cartera.resumen_ml").format(
        total=len(abiertas),
        pendientes=len(pendientes),
        convertidas=len(convertidas),
        ultimo=ultimo,
        caliente=caliente,
        vigilar=vigilar,
        no_prioritarias=no_prioritarias,
    )
    return resumen, caliente, abiertas


def construir_panel_operativo(
    i18n: I18nManager,
    repositorio: RepositorioComercialSeguroSqlite,
    cola: ColaTrabajoSeguroService,
    id_oportunidad_activa: str | None,
    filtro,
) -> tuple[str, str, str | None]:
    trabajo = cola.construir_cola_diaria()
    items = trabajo.items if filtro is None else trabajo.filtrar_por_estado(filtro)
    top = items[:5]
    texto = render_items_cola(i18n, items) or i18n.t("seguros.cola.sin_items")
    activa = top[0].id_oportunidad if top else id_oportunidad_activa
    historial = repositorio.listar_gestiones_operativas(activa or "", limite=3)
    historial_txt = render_historial_gestion(i18n, historial) or i18n.t("seguros.cola.sin_historial")
    return texto, historial_txt, activa
