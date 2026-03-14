from __future__ import annotations

from pathlib import Path

from clinicdesk.app.application.ml_artifacts.feature_artifacts import FeatureArtifactMetadata
from clinicdesk.app.application.services.ml_centro_guiado_service import CentroMLGuiadoService


class _FacadeFake:
    def __init__(self) -> None:
        self.datasets = ["v1", "v2"]
        self.models = ["m1"]
        self.model_meta = {
            "trained_on_dataset_version": "v2",
            "test_metrics": {"accuracy": 0.8, "precision": 0.77, "recall": 0.71},
        }

    def list_dataset_versions(self) -> list[str]:
        return self.datasets

    def list_model_versions(self, model_name: str = "citas_nb_v1") -> list[str]:
        return self.models

    def load_dataset_metadata(self, version: str):
        return FeatureArtifactMetadata(
            dataset_name="citas_features",
            version=version,
            created_at="2026-01-01T00:00:00+00:00",
            row_count=20,
            content_hash="abc",
            schema_hash="def",
            schema_version="v1",
            quality={"ok": True},
        )

    def load_model_metadata(self, version: str, model_name: str = "citas_nb_v1"):
        return self.model_meta


def test_playbooks_construidos_con_objetivos_reales(tmp_path: Path) -> None:
    estado = CentroMLGuiadoService(_FacadeFake()).construir_estado(tmp_path.as_posix())

    codigos = {item.codigo for item in estado.playbooks}
    assert codigos == {
        "demo_completa",
        "entrenar_modelo_nuevo",
        "puntuar_con_seguridad",
        "revisar_drift_reentrenar",
        "exportar_bi",
    }


def test_playbook_marca_recomendado_disponible_y_completado(tmp_path: Path) -> None:
    facade = _FacadeFake()
    estado = CentroMLGuiadoService(facade).construir_estado(tmp_path.as_posix())

    playbook = next(item for item in estado.playbooks if item.codigo == "entrenar_modelo_nuevo")
    estados = {paso.accion_clave: paso.estado for paso in playbook.pasos}
    assert estados["prepare"] == "completado"
    assert estados["train"] == "completado"
    assert estados["score"] in {"recomendado", "disponible", "completado"}


def test_playbook_bloquea_score_si_modelo_incompatible(tmp_path: Path) -> None:
    facade = _FacadeFake()
    facade.model_meta = {"trained_on_dataset_version": "v1"}
    estado = CentroMLGuiadoService(facade).construir_estado(tmp_path.as_posix())

    playbook = next(item for item in estado.playbooks if item.codigo == "puntuar_con_seguridad")
    paso_score = next(paso for paso in playbook.pasos if paso.accion_clave == "score")
    assert paso_score.estado == "bloqueado"
    assert paso_score.motivo_estado_key.endswith("motivo_bloqueado")


def test_playbook_drift_marca_innecesario_si_no_hay_comparacion(tmp_path: Path) -> None:
    facade = _FacadeFake()
    facade.datasets = ["v2"]
    estado = CentroMLGuiadoService(facade).construir_estado(tmp_path.as_posix())

    playbook = next(item for item in estado.playbooks if item.codigo == "revisar_drift_reentrenar")
    paso_drift = next(paso for paso in playbook.pasos if paso.accion_clave == "drift")
    assert paso_drift.estado == "innecesario"
    assert paso_drift.motivo_estado_key.endswith("motivo_drift_no_aplica")


def test_playbook_sugerido_es_coherente_con_estado(tmp_path: Path) -> None:
    facade = _FacadeFake()
    facade.datasets = []
    facade.models = []
    estado = CentroMLGuiadoService(facade).construir_estado(tmp_path.as_posix())

    assert estado.playbook_sugerido in {"demo_completa", "entrenar_modelo_nuevo", "puntuar_con_seguridad"}
