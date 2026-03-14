from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from clinicdesk.app.application.services.demo_ml_facade import CitaReadModel
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse, ScoredCita


class NivelPrioridadML(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


@dataclass(frozen=True, slots=True)
class MotivoPriorizacionML:
    codigo: str
    resumen_i18n_key: str


@dataclass(frozen=True, slots=True)
class AccionSugeridaCitaML:
    codigo: str
    descripcion_i18n_key: str
    es_accion_fuerte: bool


@dataclass(frozen=True, slots=True)
class TrazabilidadScoreML:
    score: float
    etiqueta_modelo: str
    razones_modelo: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ItemPriorizacionCitaML:
    cita_id: str
    paciente: str
    medico: str
    inicio: str
    prioridad: NivelPrioridadML
    resumen_humano_i18n_key: str
    motivo: MotivoPriorizacionML
    accion_sugerida: AccionSugeridaCitaML
    cautela_i18n_key: str
    trazabilidad: TrazabilidadScoreML
    orden_prioridad: int


@dataclass(frozen=True, slots=True)
class ResumenListaTrabajoML:
    total_items: int
    prioridad_alta: int
    prioridad_media: int
    prioridad_baja: int
    accion_fuerte_habilitada: int


@dataclass(frozen=True, slots=True)
class ListaTrabajoML:
    resumen: ResumenListaTrabajoML
    items: tuple[ItemPriorizacionCitaML, ...]


class CitasLookupPort(Protocol):
    def listar_citas(self, limite: int) -> list[CitaReadModel]: ...


class PriorizacionOperativaMLService:
    _SCORE_ALTO = 0.75
    _SCORE_MEDIO = 0.55

    def construir_lista_trabajo(
        self,
        score_response: ScoreCitasResponse,
        citas_disponibles: list[CitaReadModel],
    ) -> ListaTrabajoML:
        citas_por_id = {str(cita.id): cita for cita in citas_disponibles}
        items = [
            self._construir_item(scored=item, cita=citas_por_id.get(str(item.cita_id))) for item in score_response.items
        ]
        items_ordenados = tuple(sorted(items, key=self._ordenar_item))
        resumen = self._construir_resumen(items_ordenados)
        return ListaTrabajoML(resumen=resumen, items=items_ordenados)

    def _construir_item(self, scored: ScoredCita, cita: CitaReadModel | None) -> ItemPriorizacionCitaML:
        prioridad = self._resolver_prioridad(scored)
        accion = self._resolver_accion(scored, prioridad)
        return ItemPriorizacionCitaML(
            cita_id=str(scored.cita_id),
            paciente=cita.paciente_nombre if cita is not None else "",
            medico=cita.medico_nombre if cita is not None else "",
            inicio=cita.inicio if cita is not None else "",
            prioridad=prioridad,
            resumen_humano_i18n_key=self._resolver_resumen_humano(prioridad),
            motivo=self._resolver_motivo(scored, prioridad),
            accion_sugerida=accion,
            cautela_i18n_key=self._resolver_cautela(scored, accion),
            trazabilidad=TrazabilidadScoreML(
                score=float(scored.score),
                etiqueta_modelo=scored.label,
                razones_modelo=tuple(scored.reasons),
            ),
            orden_prioridad=self._orden_prioridad(prioridad),
        )

    def _resolver_prioridad(self, scored: ScoredCita) -> NivelPrioridadML:
        if scored.label == "risk" and scored.score >= self._SCORE_ALTO:
            return NivelPrioridadML.ALTA
        if scored.label == "risk" and scored.score >= self._SCORE_MEDIO:
            return NivelPrioridadML.MEDIA
        return NivelPrioridadML.BAJA

    def _resolver_motivo(self, scored: ScoredCita, prioridad: NivelPrioridadML) -> MotivoPriorizacionML:
        if prioridad == NivelPrioridadML.ALTA:
            return MotivoPriorizacionML("riesgo_alto", "demo_ml.priorizacion.motivo.riesgo_alto")
        if prioridad == NivelPrioridadML.MEDIA:
            return MotivoPriorizacionML("riesgo_medio", "demo_ml.priorizacion.motivo.riesgo_medio")
        return MotivoPriorizacionML("evidencia_debil", "demo_ml.priorizacion.motivo.evidencia_debil")

    def _resolver_accion(self, scored: ScoredCita, prioridad: NivelPrioridadML) -> AccionSugeridaCitaML:
        if prioridad == NivelPrioridadML.ALTA:
            return AccionSugeridaCitaML("confirmar_hoy", "demo_ml.priorizacion.accion.confirmar_hoy", True)
        if prioridad == NivelPrioridadML.MEDIA:
            return AccionSugeridaCitaML("revisar_manual", "demo_ml.priorizacion.accion.revisar_manual", False)
        if scored.label == "risk":
            return AccionSugeridaCitaML("seguimiento_suave", "demo_ml.priorizacion.accion.seguimiento_suave", False)
        return AccionSugeridaCitaML("sin_accion_fuerte", "demo_ml.priorizacion.accion.sin_accion_fuerte", False)

    def _resolver_resumen_humano(self, prioridad: NivelPrioridadML) -> str:
        mapa = {
            NivelPrioridadML.ALTA: "demo_ml.priorizacion.resumen.alta",
            NivelPrioridadML.MEDIA: "demo_ml.priorizacion.resumen.media",
            NivelPrioridadML.BAJA: "demo_ml.priorizacion.resumen.baja",
        }
        return mapa[prioridad]

    def _resolver_cautela(self, scored: ScoredCita, accion: AccionSugeridaCitaML) -> str:
        if "metadata no disponible para esta versión" in scored.reasons:
            return "demo_ml.priorizacion.cautela.metadata_incompleta"
        if scored.label != "risk":
            return "demo_ml.priorizacion.cautela.no_equivale_decision_clinica"
        if not accion.es_accion_fuerte:
            return "demo_ml.priorizacion.cautela.evidencia_aun_limitada"
        return "demo_ml.priorizacion.cautela.confirmar_contexto"

    def _ordenar_item(self, item: ItemPriorizacionCitaML) -> tuple[int, float, str]:
        return (item.orden_prioridad, -item.trazabilidad.score, item.cita_id)

    def _orden_prioridad(self, prioridad: NivelPrioridadML) -> int:
        return {
            NivelPrioridadML.ALTA: 0,
            NivelPrioridadML.MEDIA: 1,
            NivelPrioridadML.BAJA: 2,
        }[prioridad]

    def _construir_resumen(self, items: tuple[ItemPriorizacionCitaML, ...]) -> ResumenListaTrabajoML:
        altas = sum(1 for item in items if item.prioridad == NivelPrioridadML.ALTA)
        medias = sum(1 for item in items if item.prioridad == NivelPrioridadML.MEDIA)
        bajas = sum(1 for item in items if item.prioridad == NivelPrioridadML.BAJA)
        fuertes = sum(1 for item in items if item.accion_sugerida.es_accion_fuerte)
        return ResumenListaTrabajoML(
            total_items=len(items),
            prioridad_alta=altas,
            prioridad_media=medias,
            prioridad_baja=bajas,
            accion_fuerte_habilitada=fuertes,
        )
