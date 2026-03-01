from __future__ import annotations

from clinicdesk.app.application.citas_filtros_validacion import (
    MAX_RANGO_DIAS_CITAS,
    normalizar_filtros_citas,
    resolver_columnas_cita,
    validar_filtros_citas,
)


def test_validar_filtros_detecta_fechas_invertidas() -> None:
    filtros = normalizar_filtros_citas({"desde": "2025-02-01", "hasta": "2025-01-01", "estado": "TODOS"})

    resultado = validar_filtros_citas(filtros)

    assert resultado.ok is False
    assert resultado.errores[0].code == "fechas_invertidas"


def test_validar_filtros_detecta_rango_maximo() -> None:
    filtros = normalizar_filtros_citas(
        {
            "desde": "2024-01-01",
            "hasta": "2025-01-02",
            "estado": "TODOS",
        }
    )

    resultado = validar_filtros_citas(filtros)

    assert resultado.ok is False
    assert any(error.code == "rango_demasiado_grande" for error in resultado.errores)
    assert MAX_RANGO_DIAS_CITAS == 365


def test_validar_filtros_detecta_estado_id_y_texto_invalidos() -> None:
    filtros = normalizar_filtros_citas(
        {
            "desde": "2025-01-01",
            "hasta": "2025-01-31",
            "estado": "DESCONOCIDO",
            "medico_id": "0",
            "texto_busqueda": "x" * 101,
        }
    )

    resultado = validar_filtros_citas(filtros)

    codigos = {error.code for error in resultado.errores}
    assert {"estado_invalido", "id_invalido", "texto_demasiado_largo"}.issubset(codigos)


def test_pipeline_normaliza_y_luego_valida_ok() -> None:
    entrada = {
        "desde": " 2025-01-01T10:00:00 ",
        "hasta": "2025-01-31",
        "estado": " programada ",
        "texto_busqueda": "  ana  ",
        "paciente_id": " 12 ",
    }

    filtros_norm = normalizar_filtros_citas(entrada)
    resultado = validar_filtros_citas(filtros_norm)

    assert filtros_norm["desde"] == "2025-01-01"
    assert filtros_norm["estado"] == "PROGRAMADA"
    assert filtros_norm["texto_busqueda"] == "ana"
    assert filtros_norm["paciente_id"] == 12
    assert resultado.ok is True


def test_resolver_columnas_restauracion_por_settings_corrupto() -> None:
    resultado = resolver_columnas_cita(["fecha", "columna_invalida"])

    assert resultado.restauradas is True
    assert "fecha" in resultado.columnas
    assert "columna_invalida" not in resultado.columnas


def test_resolver_columnas_validas_respeta_orden() -> None:
    resultado = resolver_columnas_cita(["paciente", "estado"])

    assert resultado.restauradas is False
    assert resultado.columnas == ("paciente", "estado")
