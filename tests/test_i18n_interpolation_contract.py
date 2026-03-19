from __future__ import annotations

import logging

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.i18n_catalog import _TRANSLATIONS


def test_t_simple_permanece_compatible() -> None:
    i18n = I18nManager("es")

    assert i18n.t("comun.cerrar") == "Cerrar"


def test_t_interpola_kwargs_nombrados() -> None:
    i18n = I18nManager("es")

    assert i18n.t("dashboard_gestion.calidad.resumen", total=10, completas=7, pct="70.00") == (
        "Citas cerradas: 10 · Completas: 7 (70.00%)"
    )


def test_t_devuelve_texto_base_y_loggea_si_faltan_placeholders(caplog) -> None:
    i18n = I18nManager("es")

    with caplog.at_level(logging.WARNING):
        texto = i18n.t("dashboard_gestion.calidad.resumen", total=10, completas=7)

    assert texto == _TRANSLATIONS["es"]["dashboard_gestion.calidad.resumen"]
    assert "i18n_missing_interpolation_values" in caplog.text


def test_t_loggea_kwargs_sobrantes_sin_romper(caplog) -> None:
    i18n = I18nManager("es")

    with caplog.at_level(logging.WARNING):
        texto = i18n.t("comun.cerrar", total=10)

    assert texto == "Cerrar"
    assert "i18n_unused_interpolation_values" in caplog.text


def test_expresion_real_de_gestion_usa_interpolacion_sin_romper() -> None:
    i18n = I18nManager("es")

    resumen = i18n.t("dashboard_gestion.calidad.resumen", total=12, completas=9, pct="75.00")
    faltantes = [
        i18n.t("dashboard_gestion.calidad.faltan_check_in", total=1),
        i18n.t("dashboard_gestion.calidad.faltan_inicio_fin", total=2),
        i18n.t("dashboard_gestion.calidad.faltan_check_out", total=3),
    ]

    assert resumen == "Citas cerradas: 12 · Completas: 9 (75.00%)"
    assert faltantes == [
        "Faltan check-in: 1",
        "Falta inicio/fin de consulta: 2",
        "Falta salida: 3",
    ]


def test_expresion_real_de_citas_usa_interpolacion_sin_romper() -> None:
    i18n = I18nManager("es")

    tipo = i18n.t("citas.calidad.tipo.sin_checkin")
    banner = i18n.t("citas.calidad.banner", tipo=tipo)

    assert tipo == "sin check-in"
    assert banner == "Mostrando citas con datos incompletos: sin check-in"
