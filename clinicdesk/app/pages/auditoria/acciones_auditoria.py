from __future__ import annotations


def limpiar_filtros(ui) -> None:
    for control in (ui.input_usuario, ui.input_desde, ui.input_hasta):
        control.clear()
    for combo in (ui.combo_rango, ui.combo_accion, ui.combo_entidad):
        combo.setCurrentIndex(0)
