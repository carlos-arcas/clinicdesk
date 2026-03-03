from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO
from clinicdesk.app.application.citas.validaciones import validar_filtros_citas


def _filtros_base() -> FiltrosCitasDTO:
    return FiltrosCitasDTO(
        rango_preset="PERSONALIZADO",
        desde=datetime(2025, 1, 1, 0, 0, 0),
        hasta=datetime(2025, 1, 2, 23, 59, 59),
        limit=50,
        offset=0,
    )


def test_validar_filtros_detecta_fechas_invertidas() -> None:
    resultado = validar_filtros_citas(
        replace(_filtros_base(), desde=datetime(2025, 2, 1), hasta=datetime(2025, 1, 1)),
        "LISTA",
    )
    assert resultado.ok is False
    assert resultado.errores[0].code == "citas.fechas_invertidas"


def test_validar_filtros_detecta_rango_grande_por_contexto() -> None:
    lista = validar_filtros_citas(
        replace(_filtros_base(), desde=datetime(2025, 1, 1), hasta=datetime(2026, 1, 3)),
        "LISTA",
    )
    calendario = validar_filtros_citas(
        replace(_filtros_base(), desde=datetime(2025, 1, 1), hasta=datetime(2025, 4, 5)),
        "CALENDARIO",
    )
    assert lista.errores[0].code == "citas.rango_demasiado_grande"
    assert calendario.errores[0].code == "citas.rango_demasiado_grande"


def test_validar_filtros_detecta_texto_demasiado_largo() -> None:
    resultado = validar_filtros_citas(replace(_filtros_base(), texto_busqueda="x" * 101), "LISTA")
    assert resultado.ok is False
    assert resultado.errores[0].code == "citas.texto_demasiado_largo"


def test_validar_filtros_detecta_estado_invalido() -> None:
    resultado = validar_filtros_citas(replace(_filtros_base(), estado_cita="BAD"), "LISTA")
    assert resultado.ok is False
    assert resultado.errores[0].code == "citas.estado_invalido"


def test_validar_filtros_detecta_ids_invalidos() -> None:
    resultado = validar_filtros_citas(replace(_filtros_base(), medico_id=0), "LISTA")
    assert resultado.ok is False
    assert resultado.errores[0].code == "citas.id_invalido"


def test_validar_filtros_detecta_paginacion_invalida() -> None:
    resultado = validar_filtros_citas(replace(_filtros_base(), limit=201), "LISTA")
    assert resultado.ok is False
    assert resultado.errores[0].code == "citas.paginacion_invalida"


def test_validar_filtros_detecta_filtro_calidad_invalido() -> None:
    resultado = validar_filtros_citas(replace(_filtros_base(), filtro_calidad="BAD"), "LISTA")

    assert resultado.ok is False
    assert resultado.errores[0].code == "citas.filtro_calidad_invalido"
