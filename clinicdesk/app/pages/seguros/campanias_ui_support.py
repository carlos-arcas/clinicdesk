from __future__ import annotations

from clinicdesk.app.domain.seguros import CampaniaSeguro, ItemCampaniaSeguro
from clinicdesk.app.i18n import I18nManager


def poblar_selector_campanias_ejecutables(i18n: I18nManager, combo, campanias: tuple[CampaniaSeguro, ...]) -> None:
    combo.clear()
    for campania in campanias:
        combo.addItem(
            i18n.t("seguros.campania.selector").format(
                nombre=campania.nombre,
                estado=campania.estado.value,
                tamano=campania.tamano_lote,
            ),
            campania.id_campania,
        )


def poblar_selector_items_campania(i18n: I18nManager, combo, items: tuple[ItemCampaniaSeguro, ...]) -> None:
    combo.clear()
    for item in items:
        combo.addItem(
            i18n.t("seguros.campania.item_selector").format(
                id=item.id_oportunidad,
                estado=item.estado_trabajo.value,
                resultado=item.resultado.value,
            ),
            item.id_item,
        )


def construir_texto_resultado_campania(i18n: I18nManager, campania: CampaniaSeguro) -> str:
    r = campania.resultado_agregado
    return i18n.t("seguros.campania.resultado").format(
        nombre=campania.nombre,
        estado=campania.estado.value,
        trabajados=r.trabajados,
        total=r.total_items,
        convertidos=r.convertidos,
        rechazados=r.rechazados,
        pendientes=r.pendientes,
        ratio_conversion=f"{round(r.ratio_conversion * 100, 1)}%",
        ratio_avance=f"{round(r.ratio_avance * 100, 1)}%",
    )
