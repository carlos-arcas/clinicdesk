from __future__ import annotations

from datetime import datetime

from clinicdesk.app.application.citas import FiltrosCitasDTO, normalizar_y_validar_filtros_citas


def test_pipeline_normaliza_y_valida_ok() -> None:
    dto = FiltrosCitasDTO(rango_preset="hoy", texto_busqueda="  ana  ")
    resultado = normalizar_y_validar_filtros_citas(dto, datetime(2025, 1, 10, 9, 0, 0), "LISTA")

    assert resultado.validacion.ok is True
    assert resultado.filtros_normalizados.rango_preset == "HOY"
    assert resultado.filtros_normalizados.texto_busqueda == "ana"


def test_pipeline_falla_por_rango_calendario() -> None:
    dto = FiltrosCitasDTO(
        rango_preset="PERSONALIZADO",
        desde=datetime(2025, 1, 1, 0, 0, 0),
        hasta=datetime(2025, 4, 15, 23, 59, 59),
    )

    resultado = normalizar_y_validar_filtros_citas(dto, datetime(2025, 1, 1, 9, 0, 0), "CALENDARIO")
    assert resultado.validacion.ok is False
    assert resultado.validacion.errores[0].code == "citas.rango_demasiado_grande"
