from __future__ import annotations

from typing import Iterable

from PySide6.QtWidgets import QComboBox

from clinicdesk.app.domain.seguros import AccionPendienteSeguro, EstadoOperativoSeguro, GestionOperativaColaSeguro
from clinicdesk.app.domain.seguros.cola_operativa import ItemColaComercialSeguro
from clinicdesk.app.i18n import I18nManager


def popular_filtros_y_acciones(
    i18n: I18nManager,
    cmb_filtro_cola: QComboBox,
    cmb_accion_cola: QComboBox,
) -> None:
    cmb_filtro_cola.clear()
    cmb_filtro_cola.addItem(i18n.t("seguros.cola.filtro.todos"), None)
    for estado in EstadoOperativoSeguro:
        cmb_filtro_cola.addItem(estado.value, estado)
    cmb_accion_cola.clear()
    for accion in AccionPendienteSeguro:
        cmb_accion_cola.addItem(accion.value, accion)


def render_items_cola(i18n: I18nManager, items: tuple[ItemColaComercialSeguro, ...]) -> str:
    top = items[:5]
    return "\n".join(
        i18n.t("seguros.cola.item").format(
            id=item.id_oportunidad,
            prioridad=item.prioridad.value,
            estado=item.estado_operativo.value,
            tipo=item.tipo_item.value,
            motivo=item.motivo_principal,
            accion=item.siguiente_accion_sugerida,
        )
        for item in top
    )


def render_historial_gestion(i18n: I18nManager, historial: Iterable[GestionOperativaColaSeguro]) -> str:
    return "\n".join(
        i18n.t("seguros.cola.historial_item").format(
            accion=item.accion.value,
            estado=item.estado_resultante.value,
            nota=item.nota_corta or "-",
            siguiente=item.siguiente_paso or "-",
        )
        for item in historial
    )
