from __future__ import annotations

from datetime import datetime

import pytest

from clinicdesk.app.application.historial_paciente.filtros import (
    FiltrosHistorialPacienteDTO,
    normalizar_filtros_historial_paciente,
)


def test_normaliza_preset_30_dias_texto_y_limites() -> None:
    ahora = datetime(2026, 2, 10, 15, 30)
    filtros = FiltrosHistorialPacienteDTO(
        paciente_id=8,
        rango_preset="30_dias",
        texto="  cefalea  ",
        limite=999,
        offset=-4,
        estados=(" activa", "", "ACTIVA"),
    )

    normalizados = normalizar_filtros_historial_paciente(filtros, ahora)

    assert normalizados.rango_preset == "30_DIAS"
    assert normalizados.desde == datetime(2026, 1, 12, 0, 0)
    assert normalizados.hasta == datetime(2026, 2, 10, 23, 59, 59)
    assert normalizados.texto == "cefalea"
    assert normalizados.limite == 200
    assert normalizados.offset == 0
    assert normalizados.estados == ("ACTIVA",)


def test_normaliza_rango_personalizado_y_reordena() -> None:
    ahora = datetime(2026, 2, 10, 15, 30)
    filtros = FiltrosHistorialPacienteDTO(
        paciente_id=8,
        rango_preset="PERSONALIZADO",
        desde=datetime(2026, 3, 1, 0, 0),
        hasta=datetime(2026, 2, 1, 0, 0),
        texto="   ",
        limite=0,
        offset=None,
    )

    normalizados = normalizar_filtros_historial_paciente(filtros, ahora)

    assert normalizados.desde == datetime(2026, 2, 1, 0, 0)
    assert normalizados.hasta == datetime(2026, 3, 1, 0, 0)
    assert normalizados.texto is None
    assert normalizados.limite == 50
    assert normalizados.offset == 0


def test_normaliza_todo_sin_rango() -> None:
    ahora = datetime(2026, 2, 10, 15, 30)

    normalizados = normalizar_filtros_historial_paciente(
        FiltrosHistorialPacienteDTO(paciente_id=7, rango_preset="TODO"),
        ahora,
    )

    assert normalizados.desde is None
    assert normalizados.hasta is None


def test_falla_si_paciente_id_invalido() -> None:
    with pytest.raises(ValueError):
        normalizar_filtros_historial_paciente(FiltrosHistorialPacienteDTO(paciente_id=0), datetime(2026, 1, 1, 10, 0))
