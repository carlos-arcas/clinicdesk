from __future__ import annotations

from clinicdesk.app.application.citas.atributos import (
    ATRIBUTOS_CITA,
    formatear_valor_atributo_cita,
    obtener_columnas_default_citas,
    sanear_columnas_citas,
)


def test_atributos_cita_tienen_orden_estable_claves_unicas_e_i18n() -> None:
    claves = [atributo.clave for atributo in ATRIBUTOS_CITA]
    assert claves == [
        "fecha",
        "hora_inicio",
        "hora_fin",
        "paciente",
        "medico",
        "sala",
        "estado",
        "riesgo_ausencia",
        "duracion_estimada",
        "espera_estimada",
        "recordatorio_estado",
        "notas_len",
        "incidencias",
        "cita_id",
    ]
    assert len(claves) == len(set(claves))
    assert all(atributo.i18n_key_cabecera for atributo in ATRIBUTOS_CITA)


def test_formateadores_no_fallan_con_none() -> None:
    fila = {"inicio": None, "fin": None, "paciente": None, "notas_len": None, "tiene_incidencias": None}
    for atributo in ATRIBUTOS_CITA:
        salida = atributo.formateador_puro(fila)
        assert isinstance(salida, str)


def test_saneo_columnas_y_defaults() -> None:
    saneadas, restauradas = sanear_columnas_citas(("fecha", "foo", "fecha"))
    assert saneadas == ("fecha", "cita_id")
    assert restauradas is True

    por_defecto, restauradas_default = sanear_columnas_citas(())
    assert restauradas_default is True
    assert por_defecto == (*obtener_columnas_default_citas(), "cita_id")

    salida = formatear_valor_atributo_cita("paciente", {"paciente": "Ana López"})
    assert salida == "Ana López"
