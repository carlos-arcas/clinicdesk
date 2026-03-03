from __future__ import annotations

from datetime import date

from clinicdesk.app.application.usecases.obtener_calidad_datos import (
    UMBRAL_FALTANTES_CHECKS,
    UMBRAL_FALTANTES_INICIO_FIN,
    UMBRAL_PCT_COMPLETAS_REVISION,
    ObtenerCalidadDatos,
)
from clinicdesk.app.queries.calidad_datos_queries import FaltantesCalidadDatos


class _FakeQueries:
    def __init__(self, *, total: int, completas: int, faltantes: FaltantesCalidadDatos) -> None:
        self._total = total
        self._completas = completas
        self._faltantes = faltantes

    def contar_citas_cerradas(self, desde: date, hasta: date) -> int:
        return self._total

    def contar_completas(self, desde: date, hasta: date) -> int:
        return self._completas

    def contar_faltantes(self, desde: date, hasta: date) -> FaltantesCalidadDatos:
        return self._faltantes


def test_obtener_calidad_datos_calcula_porcentaje_y_alertas() -> None:
    uc = ObtenerCalidadDatos(
        _FakeQueries(
            total=10,
            completas=5,
            faltantes=FaltantesCalidadDatos(
                faltan_check_in=UMBRAL_FALTANTES_CHECKS + 1,
                faltan_inicio_fin=UMBRAL_FALTANTES_INICIO_FIN + 1,
                faltan_check_out=0,
            ),
        )
    )

    resultado = uc.execute(date(2024, 5, 1), date(2024, 5, 31))

    assert resultado.pct_completas == 50.0
    assert {item.code for item in resultado.alertas} == {"revision_calidad", "faltan_inicio_fin", "faltan_checks"}


def test_obtener_calidad_datos_respeta_umbrales_estrictos() -> None:
    uc = ObtenerCalidadDatos(
        _FakeQueries(
            total=10,
            completas=6,
            faltantes=FaltantesCalidadDatos(
                faltan_check_in=UMBRAL_FALTANTES_CHECKS,
                faltan_inicio_fin=UMBRAL_FALTANTES_INICIO_FIN,
                faltan_check_out=UMBRAL_FALTANTES_CHECKS,
            ),
        )
    )

    resultado = uc.execute(date(2024, 5, 1), date(2024, 5, 31))

    assert resultado.pct_completas == UMBRAL_PCT_COMPLETAS_REVISION
    assert resultado.alertas == ()
