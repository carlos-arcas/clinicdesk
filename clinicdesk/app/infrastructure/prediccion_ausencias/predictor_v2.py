from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.domain.prediccion_ausencias import (
    CitaParaPrediccion,
    NivelRiesgo,
    PrediccionAusencia,
    PredictorAusencias,
    PredictorEntrenado,
    RegistroEntrenamiento,
)

_PRIOR_ALPHA = 2.0
_PRIOR_BETA = 2.0
_PESO_PACIENTE_MAX = 0.55
_PESO_BUCKET_MAX = 0.35


@dataclass(slots=True, frozen=True)
class EstadisticaSuavizada:
    no_vino: int
    total: int

    def tasa(self) -> float:
        return (self.no_vino + _PRIOR_ALPHA) / (self.total + _PRIOR_ALPHA + _PRIOR_BETA)


@dataclass(slots=True)
class PredictorAusenciasEntrenadoV2(PredictorEntrenado):
    global_stats: EstadisticaSuavizada
    stats_por_paciente: dict[int, EstadisticaSuavizada]
    stats_por_bucket_antelacion: dict[str, EstadisticaSuavizada]

    def predecir(self, citas: list[CitaParaPrediccion]) -> list[PrediccionAusencia]:
        return [self._predecir_una(cita) for cita in citas]

    def _predecir_una(self, cita: CitaParaPrediccion) -> PrediccionAusencia:
        bucket = _bucket_antelacion(cita.dias_antelacion)
        stats_paciente = self.stats_por_paciente.get(cita.paciente_id)
        stats_bucket = self.stats_por_bucket_antelacion.get(bucket)
        probabilidad = _mezclar_probabilidades(
            prob_global=self.global_stats.tasa(),
            prob_paciente=stats_paciente.tasa() if stats_paciente else None,
            soporte_paciente=stats_paciente.total if stats_paciente else 0,
            prob_bucket=stats_bucket.tasa() if stats_bucket else None,
            soporte_bucket=stats_bucket.total if stats_bucket else 0,
        )
        return PrediccionAusencia(
            cita_id=cita.cita_id,
            riesgo=_a_nivel(probabilidad),
            explicacion_corta="Modelo jerárquico: historial global, paciente y antelación.",
        )


class PredictorAusenciasV2(PredictorAusencias):
    """Predictor probabilístico dependency-free con suavizado jerárquico."""

    def entrenar(self, dataset: list[RegistroEntrenamiento]) -> PredictorEntrenado:
        if not dataset:
            return PredictorAusenciasEntrenadoV2(
                global_stats=EstadisticaSuavizada(no_vino=0, total=0),
                stats_por_paciente={},
                stats_por_bucket_antelacion={},
            )

        global_no_vino = sum(item.no_vino for item in dataset)
        stats_por_paciente: dict[int, EstadisticaSuavizada] = {}
        stats_por_bucket_antelacion: dict[str, EstadisticaSuavizada] = {}

        for row in dataset:
            _acumular_stats(stats_por_paciente, row.paciente_id, row.no_vino)
            _acumular_stats(stats_por_bucket_antelacion, _bucket_antelacion(row.dias_antelacion), row.no_vino)

        return PredictorAusenciasEntrenadoV2(
            global_stats=EstadisticaSuavizada(no_vino=global_no_vino, total=len(dataset)),
            stats_por_paciente=stats_por_paciente,
            stats_por_bucket_antelacion=stats_por_bucket_antelacion,
        )


def _acumular_stats(destino: dict[int | str, EstadisticaSuavizada], key: int | str, no_vino: int) -> None:
    actual = destino.get(key)
    if actual is None:
        destino[key] = EstadisticaSuavizada(no_vino=no_vino, total=1)
        return
    destino[key] = EstadisticaSuavizada(no_vino=actual.no_vino + no_vino, total=actual.total + 1)


def _bucket_antelacion(dias_antelacion: int) -> str:
    if dias_antelacion <= 0:
        return "MISMO_DIA"
    if dias_antelacion <= 2:
        return "CORTA"
    if dias_antelacion <= 7:
        return "MEDIA"
    if dias_antelacion <= 13:
        return "LARGA"
    return "MUY_LARGA"


def _peso_por_soporte(soporte: int, maximo: float, escala: int) -> float:
    if soporte <= 0:
        return 0.0
    return maximo * (soporte / (soporte + escala))


def _mezclar_probabilidades(
    *,
    prob_global: float,
    prob_paciente: float | None,
    soporte_paciente: int,
    prob_bucket: float | None,
    soporte_bucket: int,
) -> float:
    peso_paciente = (
        _peso_por_soporte(soporte_paciente, _PESO_PACIENTE_MAX, escala=3) if prob_paciente is not None else 0.0
    )
    peso_bucket = _peso_por_soporte(soporte_bucket, _PESO_BUCKET_MAX, escala=4) if prob_bucket is not None else 0.0
    peso_global = max(0.0, 1.0 - peso_paciente - peso_bucket)

    estimado = peso_global * prob_global
    if prob_paciente is not None:
        estimado += peso_paciente * prob_paciente
    if prob_bucket is not None:
        estimado += peso_bucket * prob_bucket
    return min(1.0, max(0.0, estimado))


def _a_nivel(score: float) -> NivelRiesgo:
    if score >= 0.55:
        return NivelRiesgo.ALTO
    if score >= 0.3:
        return NivelRiesgo.MEDIO
    return NivelRiesgo.BAJO
