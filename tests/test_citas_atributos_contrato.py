from __future__ import annotations

from clinicdesk.app.application.citas.atributos import (
    ATRIBUTOS_CITA,
    formatear_valor_atributo_cita,
    obtener_atributos_cita_visibles_por_defecto,
)


def test_atributos_cita_tienen_orden_estable_e_i18n() -> None:
    claves = [atributo.clave for atributo in ATRIBUTOS_CITA]
    assert claves == [
        "fecha",
        "hora_inicio",
        "hora_fin",
        "paciente",
        "medico",
        "sala",
        "estado",
        "riesgo",
        "recordatorio",
        "notas_len",
        "incidencias",
    ]
    assert all(atributo.i18n_key_cabecera for atributo in ATRIBUTOS_CITA)
    assert all(atributo.i18n_key_tooltip for atributo in ATRIBUTOS_CITA)


def test_formateadores_no_fallan_con_none() -> None:
    fila = {"inicio": None, "fin": None, "paciente": None, "notas_len": None, "tiene_incidencias": None}

    for atributo in ATRIBUTOS_CITA:
        salida = atributo.formateador_presentacion(fila)
        assert isinstance(salida, str)


def test_helpers_atributos_visibles_y_formateo() -> None:
    visibles = obtener_atributos_cita_visibles_por_defecto()
    claves_visibles = [item.clave for item in visibles]
    assert "riesgo" not in claves_visibles
    assert "recordatorio" not in claves_visibles

    salida = formatear_valor_atributo_cita("paciente", {"paciente": "Ana López"})
    assert salida == "Ana López"
