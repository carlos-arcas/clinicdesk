from __future__ import annotations

from dataclasses import dataclass
from statistics import quantiles

from clinicdesk.app.domain.prediccion_operativa import CitaOperativa, NivelRiesgo, PrediccionOperativa, PredictorOperativo, RegistroOperativo

_MIN_EJEMPLOS_CLAVE = 30


@dataclass(frozen=True, slots=True)
class Umbrales:
    p33: float
    p66: float
    n: int


@dataclass(slots=True)
class ModeloOperativoBaseline:
    por_clave: dict[tuple[int, str | None, str | None, int | None], Umbrales]
    globales: Umbrales
    ultimos_motivos: dict[int, tuple[str, ...]]

    def predecir(self, citas: list[CitaOperativa]) -> list[PrediccionOperativa]:
        predicciones = [self._predecir_una(cita) for cita in citas]
        self.ultimos_motivos = {x.cita_id: x.reason_codes for x in predicciones}
        return predicciones

    def _predecir_una(self, cita: CitaOperativa) -> PrediccionOperativa:
        clave = _clave(cita.medico_id, cita.tipo_cita, cita.franja_hora, cita.dia_semana)
        umbrales = self.por_clave.get(clave)
        minutos_ref = _valor_estimado(cita.franja_hora, umbrales or self.globales)
        nivel = _a_nivel(minutos_ref, umbrales or self.globales)
        reasons = ["MEDICO_PATRON_ALTO"] if umbrales else ["FALLBACK_GLOBAL"]
        if cita.franja_hora in {"12-16", "16-20"}:
            reasons.append("FRANJA_DEMANDA")
        return PrediccionOperativa(cita_id=cita.cita_id, nivel=nivel, reason_codes=tuple(reasons[:3]))


class PredictorOperativoBaseline(PredictorOperativo):
    def entrenar(self, dataset: list[RegistroOperativo]) -> ModeloOperativoBaseline:
        if not dataset:
            return ModeloOperativoBaseline({}, Umbrales(p33=10.0, p66=20.0, n=0), {})
        globales = _calcular_umbrales([x.minutos for x in dataset])
        agrupado: dict[tuple[int, str | None, str | None, int | None], list[float]] = {}
        for item in dataset:
            clave = _clave(item.medico_id, item.tipo_cita, item.franja_hora, item.dia_semana)
            agrupado.setdefault(clave, []).append(item.minutos)
        por_clave = {
            clave: _calcular_umbrales(valores)
            for clave, valores in agrupado.items()
            if len(valores) >= _MIN_EJEMPLOS_CLAVE
        }
        return ModeloOperativoBaseline(por_clave=por_clave, globales=globales, ultimos_motivos={})


def _clave(medico_id: int, tipo_cita: str | None, franja_hora: str | None, dia_semana: int | None) -> tuple[int, str | None, str | None, int | None]:
    return medico_id, tipo_cita, franja_hora, dia_semana


def _calcular_umbrales(valores: list[float]) -> Umbrales:
    if len(valores) < 3:
        base = max(valores[0], 1.0) if valores else 1.0
        return Umbrales(p33=base, p66=base * 1.5, n=len(valores))
    q33, q66 = quantiles(valores, n=3, method="inclusive")
    return Umbrales(p33=max(1.0, q33), p66=max(q33, q66), n=len(valores))


def _a_nivel(valor: float, umbrales: Umbrales) -> NivelRiesgo:
    if valor <= umbrales.p33:
        return NivelRiesgo.BAJO
    if valor <= umbrales.p66:
        return NivelRiesgo.MEDIO
    return NivelRiesgo.ALTO


def _valor_estimado(franja_hora: str | None, umbrales: Umbrales) -> float:
    if franja_hora == "08-12":
        return umbrales.p33
    if franja_hora == "16-20":
        return umbrales.p66 + 1
    return (umbrales.p33 + umbrales.p66) / 2
