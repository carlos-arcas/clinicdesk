from __future__ import annotations

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.formularios_validacion import (
    primer_campo_con_error,
    validar_formulario_cita,
    validar_formulario_paciente,
)


def test_validar_formulario_paciente_requeridos_y_email() -> None:
    i18n = I18nManager("es")

    errores = validar_formulario_paciente(
        {"documento": "", "nombre": "", "apellidos": "", "email": "invalido"},
        i18n=i18n,
    )

    assert set(errores) == {"documento", "nombre", "apellidos", "email"}


def test_validar_formulario_cita_requeridos() -> None:
    i18n = I18nManager("es")

    errores = validar_formulario_cita(
        {"paciente_id": "", "medico_id": "", "sala_id": "", "inicio": "", "fin": ""},
        i18n=i18n,
    )

    assert set(errores) == {"inicio", "fin"}


def test_primer_campo_con_error_respeta_orden() -> None:
    campo = primer_campo_con_error({"fin": "x", "inicio": "x"}, ["inicio", "fin"])
    assert campo == "inicio"
