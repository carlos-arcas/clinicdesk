from __future__ import annotations

from datetime import datetime

from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO, normalizar_filtros_citas


def test_normalizar_filtros_aplica_defaults_trim_y_ids() -> None:
    ahora = datetime(2025, 1, 10, 11, 45)
    filtros = FiltrosCitasDTO(
        rango_preset="  desconocido ",
        texto_busqueda="   ",
        estado_cita=" todos ",
        medico_id=-1,
        recordatorio_filtro="no_enviado",
        limit=999,
        offset=-10,
    )

    normalizados = normalizar_filtros_citas(filtros, ahora)

    assert normalizados.rango_preset == "HOY"
    assert normalizados.desde == datetime(2025, 1, 10, 0, 0)
    assert normalizados.hasta == datetime(2025, 1, 10, 23, 59, 59)
    assert normalizados.texto_busqueda is None
    assert normalizados.estado_cita is None
    assert normalizados.medico_id is None
    assert normalizados.recordatorio_filtro == "NO_ENVIADO"
    assert normalizados.limit == 200
    assert normalizados.offset == 0


def test_normalizar_filtros_corrige_rango_personalizado_invertido() -> None:
    ahora = datetime(2025, 1, 10, 11, 45)
    filtros = FiltrosCitasDTO(
        rango_preset="PERSONALIZADO",
        desde=datetime(2025, 12, 1, 0, 0),
        hasta=datetime(2025, 1, 10, 0, 0),
    )

    normalizados = normalizar_filtros_citas(filtros, ahora)

    assert normalizados.desde == datetime(2025, 1, 10, 0, 0)
    assert normalizados.hasta == datetime(2025, 12, 1, 0, 0)


def test_normalizar_filtros_semana_y_mes() -> None:
    ahora = datetime(2024, 2, 15, 8, 0)

    semana = normalizar_filtros_citas(FiltrosCitasDTO(rango_preset="SEMANA"), ahora)
    mes = normalizar_filtros_citas(FiltrosCitasDTO(rango_preset="MES"), ahora)

    assert semana.desde == datetime(2024, 2, 15, 0, 0)
    assert semana.hasta == datetime(2024, 2, 21, 23, 59, 59)
    assert mes.desde == datetime(2024, 2, 1, 0, 0)
    assert mes.hasta == datetime(2024, 2, 29, 23, 59, 59)


def test_normalizar_filtro_calidad_catalogo() -> None:
    ahora = datetime(2025, 1, 10, 11, 45)

    valido = normalizar_filtros_citas(FiltrosCitasDTO(filtro_calidad="sin_checkin"), ahora)
    invalido = normalizar_filtros_citas(FiltrosCitasDTO(filtro_calidad="otra"), ahora)

    assert valido.filtro_calidad == "SIN_CHECKIN"
    assert invalido.filtro_calidad is None
