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


@dataclass(slots=True)
class PredictorAusenciasEntrenadoBaseline(PredictorEntrenado):
    tasa_global: float
    tasa_por_paciente: dict[int, float]

    def predecir(self, citas: list[CitaParaPrediccion]) -> list[PrediccionAusencia]:
        return [self._predecir_una(cita) for cita in citas]

    def _predecir_una(self, cita: CitaParaPrediccion) -> PrediccionAusencia:
        tasa = self.tasa_por_paciente.get(cita.paciente_id, self.tasa_global)
        score = _ajustar_por_antelacion(tasa, cita.dias_antelacion)
        return PrediccionAusencia(
            cita_id=cita.cita_id,
            riesgo=_a_nivel(score),
            explicacion_corta="Basado en historial de asistencia y antelación.",
        )


class PredictorAusenciasBaseline(PredictorAusencias):
    """Predictor simple sin dependencias externas."""

    def entrenar(self, dataset: list[RegistroEntrenamiento]) -> PredictorEntrenado:
        if not dataset:
            return PredictorAusenciasEntrenadoBaseline(tasa_global=0.15, tasa_por_paciente={})

        global_total = len(dataset)
        global_no_vino = sum(item.no_vino for item in dataset)
        tasa_global = (global_no_vino + 2) / (global_total + 4)

        por_paciente: dict[int, list[int]] = {}
        for row in dataset:
            por_paciente.setdefault(row.paciente_id, []).append(row.no_vino)

        tasas = {
            paciente_id: (sum(values) + 1) / (len(values) + 2)
            for paciente_id, values in por_paciente.items()
        }
        return PredictorAusenciasEntrenadoBaseline(tasa_global=tasa_global, tasa_por_paciente=tasas)


def _ajustar_por_antelacion(base: float, dias_antelacion: int) -> float:
    if dias_antelacion <= 0:
        return min(1.0, base + 0.12)
    if dias_antelacion <= 2:
        return min(1.0, base + 0.06)
    if dias_antelacion >= 14:
        return max(0.0, base - 0.05)
    return base


def _a_nivel(score: float) -> NivelRiesgo:
    if score >= 0.55:
        return NivelRiesgo.ALTO
    if score >= 0.3:
        return NivelRiesgo.MEDIO
    return NivelRiesgo.BAJO
