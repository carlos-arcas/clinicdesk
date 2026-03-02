from __future__ import annotations

from clinicdesk.app.application.historial_paciente.atributos import (
    ATRIBUTOS_HISTORIAL_CITAS,
    ATRIBUTOS_HISTORIAL_RECETAS,
    obtener_columnas_default_historial_citas,
    obtener_columnas_default_historial_recetas,
    sanear_columnas_solicitadas,
)


def test_contratos_atributos_tienen_claves_unicas_i18n_y_formatean_none() -> None:
    for contrato in (ATRIBUTOS_HISTORIAL_CITAS, ATRIBUTOS_HISTORIAL_RECETAS):
        claves = [item.clave for item in contrato]
        assert len(claves) == len(set(claves))
        assert all(item.i18n_key_cabecera for item in contrato)
        for item in contrato:
            assert item.formateador({}) is not None


def test_columnas_default_orden_estable() -> None:
    assert obtener_columnas_default_historial_citas() == (
        "fecha",
        "hora_inicio",
        "estado",
        "medico",
        "tiene_incidencias",
    )
    assert obtener_columnas_default_historial_recetas() == (
        "fecha",
        "estado",
        "medico",
        "num_lineas",
        "activa",
    )


def test_sanear_columnas_hace_fallback_si_hay_corrupcion() -> None:
    saneadas, restauradas = sanear_columnas_solicitadas(("foo", "bar"), ATRIBUTOS_HISTORIAL_CITAS)

    assert saneadas == obtener_columnas_default_historial_citas()
    assert restauradas is True

    sanas, restauradas = sanear_columnas_solicitadas(("cita_id", "estado"), ATRIBUTOS_HISTORIAL_CITAS)
    assert sanas == ("cita_id", "estado")
    assert restauradas is False


def test_sanear_columnas_elimina_duplicados_y_desconocidas() -> None:
    saneadas, restauradas = sanear_columnas_solicitadas(("estado", "foo", "estado", "medico"), ATRIBUTOS_HISTORIAL_CITAS)
    assert saneadas == ("estado", "medico")
    assert restauradas is True
