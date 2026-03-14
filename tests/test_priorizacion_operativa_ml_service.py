from __future__ import annotations

from clinicdesk.app.application.services.demo_ml_facade import CitaReadModel
from clinicdesk.app.application.services.priorizacion_operativa_ml_service import (
    NivelPrioridadML,
    PriorizacionOperativaMLService,
)
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse, ScoredCita


def _score_item(cita_id: str, score: float, label: str = "risk", reasons: list[str] | None = None) -> ScoredCita:
    return ScoredCita(cita_id=cita_id, score=score, label=label, reasons=reasons or ["predictor:baseline"])


def _cita(cita_id: int) -> CitaReadModel:
    return CitaReadModel(
        id=cita_id,
        inicio="2026-03-10T09:00:00",
        fin="2026-03-10T09:30:00",
        paciente_nombre=f"Paciente {cita_id}",
        medico_nombre="Dra. Demo",
        estado="programada",
        motivo="control",
    )


def test_priorizacion_construye_lista_con_contrato_explicito() -> None:
    service = PriorizacionOperativaMLService()
    score = ScoreCitasResponse(
        version="v1",
        total=2,
        items=[_score_item("10", 0.82), _score_item("11", 0.60)],
    )

    lista = service.construir_lista_trabajo(score, [_cita(10), _cita(11)])

    assert lista.resumen.total_items == 2
    assert lista.items[0].cita_id == "10"
    assert lista.items[0].prioridad == NivelPrioridadML.ALTA
    assert lista.items[0].accion_sugerida.es_accion_fuerte is True
    assert lista.items[0].motivo.codigo == "riesgo_alto"


def test_priorizacion_ordena_por_prioridad_y_score_descendente() -> None:
    service = PriorizacionOperativaMLService()
    score = ScoreCitasResponse(
        version="v2",
        total=3,
        items=[
            _score_item("1", 0.57),
            _score_item("2", 0.93),
            _score_item("3", 0.51),
        ],
    )

    lista = service.construir_lista_trabajo(score, [_cita(1), _cita(2), _cita(3)])

    assert [item.cita_id for item in lista.items] == ["2", "1", "3"]
    assert lista.resumen.prioridad_alta == 1
    assert lista.resumen.prioridad_media == 1
    assert lista.resumen.prioridad_baja == 1


def test_guardrail_sin_base_suficiente_no_sugiere_accion_fuerte() -> None:
    service = PriorizacionOperativaMLService()
    score = ScoreCitasResponse(
        version="v3",
        total=1,
        items=[_score_item("22", 0.40, label="no_risk", reasons=["metadata no disponible para esta versión"])],
    )

    lista = service.construir_lista_trabajo(score, [_cita(22)])
    item = lista.items[0]

    assert item.prioridad == NivelPrioridadML.BAJA
    assert item.accion_sugerida.codigo == "sin_accion_fuerte"
    assert item.accion_sugerida.es_accion_fuerte is False
    assert item.cautela_i18n_key == "demo_ml.priorizacion.cautela.metadata_incompleta"


def test_priorizacion_tolerante_si_falta_read_model_de_cita() -> None:
    service = PriorizacionOperativaMLService()
    score = ScoreCitasResponse(version="v4", total=1, items=[_score_item("404", 0.80)])

    lista = service.construir_lista_trabajo(score, [])

    assert lista.items[0].paciente == ""
    assert lista.items[0].medico == ""
