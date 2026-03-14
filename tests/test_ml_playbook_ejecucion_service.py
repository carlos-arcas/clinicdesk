from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.evaluation import EvalMetrics
from clinicdesk.app.application.services.ml_playbook_ejecucion_service import (
    ContextoEjecucionPlaybook,
    PlaybookEjecucionService,
)
from clinicdesk.app.application.services.ml_playbooks_service import PlaybookML, PasoPlaybookML
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse, ScoredCita
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModelResponse


@dataclass(slots=True)
class _FacadeFake:
    datasets: list[str]
    models: list[str]

    def build_features(self, from_date: str, to_date: str, version: str | None = None) -> str:
        self.datasets.append("v3")
        return "v3"

    def list_dataset_versions(self) -> list[str]:
        return self.datasets

    def train(self, dataset_version: str, model_version: str | None = None) -> TrainCitasModelResponse:
        metrics = EvalMetrics(accuracy=0.8, precision=0.7, recall=0.6, tp=1, fp=1, tn=1, fn=1)
        self.models.append("m2")
        return TrainCitasModelResponse(
            model_name="citas_nb_v1",
            model_version="m2",
            dataset_version=dataset_version,
            train_metrics=metrics,
            test_metrics=metrics,
            calibrated_threshold=0.5,
            test_metrics_at_calibrated_threshold=metrics,
        )

    def list_model_versions(self) -> list[str]:
        return self.models

    def score(self, dataset_version: str, predictor_kind: str, model_version: str, limit: int) -> ScoreCitasResponse:
        return ScoreCitasResponse(
            version=dataset_version,
            total=2,
            items=[
                ScoredCita(cita_id="1", score=0.7, label="risk", reasons=[]),
                ScoredCita(cita_id="2", score=0.2, label="ok", reasons=[]),
            ],
        )

    def drift(self, from_version: str, to_version: str) -> DriftReport:
        return DriftReport(
            from_version=from_version,
            to_version=to_version,
            total_from=10,
            total_to=12,
            feature_shifts={"edad": {"a": 0.1}},
            psi_by_feature={"edad": 0.2},
            overall_flag=True,
        )


def _playbook(estado_paso: str = "recomendado", accion: str = "prepare") -> PlaybookML:
    paso = PasoPlaybookML(
        clave=f"demo.{accion}",
        accion_clave=accion,
        nombre_key="n",
        que_hace_key="q",
        por_que_importa_key="p",
        necesitas_key="ne",
        resultado_key="r",
        mirar_despues_key="m",
        cta_key="cta",
        estado=estado_paso,
        habilitado=True,
        motivo_estado_key="motivo",
    )
    return PlaybookML(
        codigo="demo",
        titulo_key="t",
        descripcion_key="d",
        para_que_key="pq",
        cuando_usar_key="cu",
        prerequisitos_keys=(),
        criterio_finalizacion_key="f",
        estado_general="activo",
        siguiente_paso_clave=accion,
        pasos=(paso,),
    )


def test_construir_estado_marca_accion_directa_y_progreso() -> None:
    service = PlaybookEjecucionService(_FacadeFake(datasets=["v1", "v2"], models=["m1"]))

    estado = service.construir_estado(_playbook("recomendado", "train"))

    assert estado.accion_siguiente.permiso == "directa"
    assert estado.progreso.total_pasos == 1
    assert estado.progreso.ejecutables == 1


def test_construir_estado_pide_confirmacion_si_paso_completado() -> None:
    service = PlaybookEjecucionService(_FacadeFake(datasets=["v1"], models=["m1"]))

    estado = service.construir_estado(_playbook("completado", "score"))

    assert estado.accion_siguiente.permiso == "requiere_confirmacion"
    assert estado.accion_siguiente.requiere_confirmacion is True


def test_ejecutar_prepare_genera_resultado_humano() -> None:
    facade = _FacadeFake(datasets=["v1", "v2"], models=["m1"])
    service = PlaybookEjecucionService(facade)
    accion = service.construir_estado(_playbook("recomendado", "prepare")).accion_siguiente

    resultado = service.ejecutar_accion(
        accion,
        ContextoEjecucionPlaybook(from_date="2026-01-01", to_date="2026-01-31", score_limit=5, export_dir="./exports"),
    )

    assert resultado.estado == "completado"
    assert "Dataset generado" in resultado.detalle_humano


def test_guardrail_bloquea_si_accion_no_permitida() -> None:
    service = PlaybookEjecucionService(_FacadeFake(datasets=["v1"], models=[]))
    accion = service.construir_estado(_playbook("bloqueado", "score")).accion_siguiente

    try:
        service.ejecutar_accion(
            accion,
            ContextoEjecucionPlaybook(from_date="2026-01-01", to_date="2026-01-31", score_limit=10, export_dir="./exports"),
        )
    except ValueError as exc:
        assert "bloqueada" in str(exc)
    else:
        raise AssertionError("Debía bloquear la ejecución")


def test_reintento_disponible_cuando_falla_por_prerequisito() -> None:
    service = PlaybookEjecucionService(_FacadeFake(datasets=["v1"], models=[]))
    accion = service.construir_estado(_playbook("recomendado", "score")).accion_siguiente

    resultado = service.ejecutar_accion(
        accion,
        ContextoEjecucionPlaybook(from_date="2026-01-01", to_date="2026-01-31", score_limit=10, export_dir="./exports"),
    )

    assert resultado.estado == "fallido"
    assert resultado.reintento_permitido is True
