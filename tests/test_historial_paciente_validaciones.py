from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from clinicdesk.app.application.historial_paciente.filtros import (
    FiltrosHistorialPacienteDTO,
    normalizar_filtros_historial_paciente,
)
from clinicdesk.app.application.historial_paciente.validaciones import validar_filtros_historial_paciente


def _filtros_base() -> FiltrosHistorialPacienteDTO:
    return FiltrosHistorialPacienteDTO(
        paciente_id=7,
        rango_preset="PERSONALIZADO",
        desde=datetime(2025, 1, 1, 0, 0),
        hasta=datetime(2025, 1, 31, 23, 59),
        texto="ok",
        estados=("PROGRAMADA",),
        limite=50,
        offset=0,
    )


def test_valida_fechas_invertidas() -> None:
    filtros = replace(_filtros_base(), desde=datetime(2025, 2, 1), hasta=datetime(2025, 1, 1))
    resultado = validar_filtros_historial_paciente(filtros, "citas")
    assert resultado.ok is False
    assert resultado.errores[0].code == "historial.fechas_invertidas"


def test_valida_rango_demasiado_grande() -> None:
    filtros = replace(_filtros_base(), hasta=datetime(2028, 1, 1))
    resultado = validar_filtros_historial_paciente(filtros, "citas")
    assert any(error.code == "historial.rango_demasiado_grande" for error in resultado.errores)


def test_valida_texto_demasiado_largo() -> None:
    filtros = replace(_filtros_base(), texto="x" * 101)
    resultado = validar_filtros_historial_paciente(filtros, "citas")
    assert any(error.code == "historial.texto_demasiado_largo" for error in resultado.errores)


def test_valida_estado_invalido_por_pestana() -> None:
    filtros = replace(_filtros_base(), estados=("ACTIVA",))
    resultado = validar_filtros_historial_paciente(filtros, "citas")
    assert any(error.code == "historial.estado_invalido" for error in resultado.errores)


def test_valida_paginacion_invalida() -> None:
    filtros = replace(_filtros_base(), limite=500, offset=-1)
    resultado = validar_filtros_historial_paciente(filtros, "citas")
    assert any(error.code == "historial.paginacion_invalida" for error in resultado.errores)


def test_integracion_normalizar_y_validar() -> None:
    bruto = FiltrosHistorialPacienteDTO(
        paciente_id=7, rango_preset="30_dias", texto="  dolor  ", estados=("programada",), limite=50, offset=0
    )
    normalizados = normalizar_filtros_historial_paciente(bruto, datetime(2026, 2, 10, 10, 0))
    resultado = validar_filtros_historial_paciente(normalizados, "citas")
    assert normalizados.texto == "dolor"
    assert resultado.ok is True
