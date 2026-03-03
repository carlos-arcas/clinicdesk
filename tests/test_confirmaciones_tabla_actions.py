from __future__ import annotations

from clinicdesk.app.pages.confirmaciones.acciones_whatsapp_rapido import estado_accion_whatsapp_rapida


def test_estado_accion_whatsapp_rapida_combinaciones_clave() -> None:
    alto_ok = estado_accion_whatsapp_rapida("ALTO", "SIN_PREPARAR", True)
    assert alto_ok.visible is True
    assert alto_ok.enabled is True
    assert alto_ok.tooltip_key is None

    alto_sin_tel = estado_accion_whatsapp_rapida("ALTO", "SIN_PREPARAR", False)
    assert (alto_sin_tel.visible, alto_sin_tel.enabled) == (True, False)
    assert alto_sin_tel.tooltip_key == "confirmaciones.accion.falta_telefono"

    alto_enviado = estado_accion_whatsapp_rapida("ALTO", "ENVIADO", True)
    assert (alto_enviado.visible, alto_enviado.enabled) == (True, False)
    assert alto_enviado.tooltip_key == "confirmaciones.accion.ya_enviado"

    alto_preparado = estado_accion_whatsapp_rapida("ALTO", "PREPARADO", True)
    assert (alto_preparado.visible, alto_preparado.enabled) == (True, False)
    assert alto_preparado.tooltip_key == "confirmaciones.accion.ya_preparado"

    medio = estado_accion_whatsapp_rapida("MEDIO", "SIN_PREPARAR", True)
    assert (medio.visible, medio.enabled) == (False, False)

    bajo = estado_accion_whatsapp_rapida("BAJO", "SIN_PREPARAR", True)
    assert (bajo.visible, bajo.enabled) == (False, False)
