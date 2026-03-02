from __future__ import annotations

from clinicdesk.app.application.citas import formatear_valor_atributo_cita, redactar_texto_busqueda
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.widgets.tooltip_citas import construir_tooltip_cita


def test_notas_len_nunca_expone_texto_sensible() -> None:
    fila = {"notas_len": "texto muy sensible"}

    salida = formatear_valor_atributo_cita("notas_len", fila)

    assert salida != "texto muy sensible"
    assert salida == str(len("texto muy sensible"))


def test_tooltip_no_incluye_texto_sensible_ni_contacto() -> None:
    fila = {
        "inicio": "2026-02-01T09:00:00",
        "fin": "2026-02-01T09:30:00",
        "paciente": "Paciente Demo",
        "medico": "Medico Demo",
        "sala": "S1",
        "estado": "PROGRAMADA",
        "riesgo_ausencia": "BAJO",
        "recordatorio_estado": "NO_ENVIADO",
        "tiene_incidencias": "NO",
        "notas_len": "nota privada sensible",
        "notas": "nota privada sensible",
        "email": "persona@example.com",
        "telefono": "+34 600 123 123",
    }

    tooltip = construir_tooltip_cita(I18nManager("es"), fila)

    assert "nota privada sensible" not in tooltip
    assert "persona@example.com" not in tooltip
    assert "+34 600 123 123" not in tooltip


def test_redactar_texto_busqueda_no_devuelve_texto_completo() -> None:
    texto = "mi dni 12345678Z"

    redaccion = redactar_texto_busqueda(texto)

    assert redaccion != texto
    assert redaccion == "mi dni 12345…"
