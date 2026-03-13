from __future__ import annotations

from pathlib import Path

from clinicdesk.app.application.ml_artifacts.feature_artifacts import FeatureArtifactMetadata
from clinicdesk.app.application.services.ml_centro_guiado_service import CentroMLGuiadoService


class _FacadeFake:
    def __init__(self) -> None:
        self.datasets = ["v1", "v2"]
        self.models = ["m1"]

    def list_dataset_versions(self) -> list[str]:
        return self.datasets

    def list_model_versions(self, model_name: str = "citas_nb_v1") -> list[str]:
        return self.models

    def load_dataset_metadata(self, version: str):
        return FeatureArtifactMetadata(
            dataset_name="citas_features",
            version=version,
            created_at="2026-01-01T00:00:00+00:00",
            row_count=10,
            content_hash="abc",
            schema_hash="def",
            schema_version="v1",
            quality={"ok": True},
        )

    def load_model_metadata(self, version: str, model_name: str = "citas_nb_v1"):
        return {"trained_on_dataset_version": "v2"}


def test_estado_centro_ml_habilita_score_y_drift_si_hay_prerequisitos(tmp_path: Path) -> None:
    facade = _FacadeFake()
    (tmp_path / "scoring_export.csv").write_text("ok", encoding="utf-8")

    estado = CentroMLGuiadoService(facade).construir_estado(tmp_path.as_posix())

    assert estado.score_disponible is True
    assert estado.drift_disponible is True
    assert estado.siguiente_accion in {"score", "drift", "export"}


def test_estado_centro_ml_bloquea_score_si_modelo_no_compatible(tmp_path: Path) -> None:
    facade = _FacadeFake()
    facade.load_model_metadata = lambda version, model_name="citas_nb_v1": {"trained_on_dataset_version": "otra"}

    estado = CentroMLGuiadoService(facade).construir_estado(tmp_path.as_posix())

    assert estado.score_disponible is False
    paso_score = next(p for p in estado.pasos if p.clave == "score")
    assert paso_score.habilitado is False
    assert "compatibles" in paso_score.motivo_bloqueo
