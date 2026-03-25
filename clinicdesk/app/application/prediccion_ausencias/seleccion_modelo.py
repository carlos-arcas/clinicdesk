from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResultadoMetricasModelo:
    model_type: str
    accuracy: float
    recall_no_show: float
    f1_no_show: float


@dataclass(frozen=True, slots=True)
class ResultadoSeleccionModelo:
    ganador: ResultadoMetricasModelo
    baseline: ResultadoMetricasModelo
    candidato_v2: ResultadoMetricasModelo
    criterio: str


def seleccionar_mejor_modelo(
    *,
    baseline: ResultadoMetricasModelo,
    candidato_v2: ResultadoMetricasModelo,
) -> ResultadoSeleccionModelo:
    """Criterio determinista: f1 > recall > accuracy > baseline por estabilidad."""
    if _clave_orden(candidato_v2) > _clave_orden(baseline):
        ganador = candidato_v2
    else:
        ganador = baseline

    return ResultadoSeleccionModelo(
        ganador=ganador,
        baseline=baseline,
        candidato_v2=candidato_v2,
        criterio="f1_no_show > recall_no_show > accuracy > baseline_en_empate",
    )


def _clave_orden(resultado: ResultadoMetricasModelo) -> tuple[float, float, float]:
    return (
        resultado.f1_no_show,
        resultado.recall_no_show,
        resultado.accuracy,
    )
