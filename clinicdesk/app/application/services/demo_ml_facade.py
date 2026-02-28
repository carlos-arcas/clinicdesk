from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from clinicdesk.app.application.features.citas_features import (
    build_citas_features,
    compute_citas_quality_report,
)
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.pipelines.build_citas_dataset import BuildCitasDataset
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.usecases.drift_citas_features import (
    DriftCitasFeatures,
    DriftCitasFeaturesRequest,
)
from clinicdesk.app.application.usecases.export_csv import (
    ExportDriftCSV,
    ExportFeaturesCSV,
    ExportModelMetricsCSV,
    ExportScoringCSV,
)
from clinicdesk.app.application.usecases.score_citas import (
    ScoreCitas,
    ScoreCitasRequest,
    ScoreCitasResponse,
)
from clinicdesk.app.application.usecases.seed_demo_data import (
    SeedDemoData,
    SeedDemoDataRequest,
    SeedDemoDataResponse,
)
from clinicdesk.app.application.usecases.train_citas_model import (
    TrainCitasModel,
    TrainCitasModelRequest,
    TrainCitasModelResponse,
)


@dataclass(slots=True, frozen=True)
class DoctorReadModel:
    id: int
    documento: str
    nombre_completo: str
    telefono: str
    especialidad: str
    activo: bool


@dataclass(slots=True, frozen=True)
class PatientReadModel:
    id: int
    documento: str
    nombre_completo: str
    telefono: str
    activo: bool


@dataclass(slots=True, frozen=True)
class CitaReadModel:
    id: int
    inicio: str
    fin: str
    paciente_nombre: str
    medico_nombre: str
    estado: str
    motivo: str


@dataclass(slots=True, frozen=True)
class IncidenceReadModel:
    id: int
    fecha_hora: str
    tipo: str
    severidad: str
    estado: str
    descripcion: str


class DemoMLReadGateway(Protocol):
    def list_doctors(self, query: str | None, limit: int) -> list[dict[str, Any]]: ...

    def list_patients(self, query: str | None, limit: int) -> list[dict[str, Any]]: ...

    def list_appointments(
        self,
        query: str | None,
        from_date: str | None,
        to_date: str | None,
        limit: int,
    ) -> list[dict[str, Any]]: ...

    def list_incidences(self, query: str | None, limit: int) -> list[dict[str, Any]]: ...


class DemoMLFacade:
    def __init__(
        self,
        read_gateway: DemoMLReadGateway,
        seed_demo_uc: SeedDemoData,
        build_dataset: BuildCitasDataset,
        feature_store_service: FeatureStoreService,
        train_uc: TrainCitasModel,
        score_uc: ScoreCitas,
        drift_uc: DriftCitasFeatures,
    ) -> None:
        self._read_gateway = read_gateway
        self._seed_demo_uc = seed_demo_uc
        self._build_dataset = build_dataset
        self._feature_store_service = feature_store_service
        self._train_uc = train_uc
        self._score_uc = score_uc
        self._drift_uc = drift_uc
        self._export_features = ExportFeaturesCSV()
        self._export_metrics = ExportModelMetricsCSV()
        self._export_scoring = ExportScoringCSV()
        self._export_drift = ExportDriftCSV()

    def seed_demo(self, req: SeedDemoDataRequest) -> SeedDemoDataResponse:
        return self._seed_demo_uc.execute(req)

    def list_doctors(self, query: str | None = None, limit: int = 100) -> list[DoctorReadModel]:
        rows = self._read_gateway.list_doctors(query, limit)
        return [DoctorReadModel(**row) for row in rows]

    def list_patients(self, query: str | None = None, limit: int = 100) -> list[PatientReadModel]:
        rows = self._read_gateway.list_patients(query, limit)
        return [PatientReadModel(**row) for row in rows]

    def list_appointments(
        self,
        query: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
    ) -> list[CitaReadModel]:
        rows = self._read_gateway.list_appointments(query, from_date, to_date, limit)
        return [CitaReadModel(**row) for row in rows]

    def list_incidences(self, query: str | None = None, limit: int = 100) -> list[IncidenceReadModel]:
        rows = self._read_gateway.list_incidences(query, limit)
        return [IncidenceReadModel(**row) for row in rows]

    def build_features(self, from_date: str, to_date: str, version: str | None = None) -> str:
        desde = datetime.fromisoformat(f"{from_date}T00:00:00")
        hasta = datetime.fromisoformat(f"{to_date}T23:59:59")
        dataset_rows = self._build_dataset.execute(desde, hasta)
        features = build_citas_features(dataset_rows)
        quality = compute_citas_quality_report(features)
        return self._feature_store_service.save_citas_features_with_artifacts(features, quality, version=version)

    def train(self, dataset_version: str, model_version: str | None = None) -> TrainCitasModelResponse:
        request = TrainCitasModelRequest(dataset_version=dataset_version, model_version=model_version)
        return self._train_uc.execute(request)

    def score(
        self,
        dataset_version: str,
        predictor_kind: str = "baseline",
        model_version: str | None = None,
        limit: int | None = None,
    ) -> ScoreCitasResponse:
        request = ScoreCitasRequest(
            dataset_version=dataset_version,
            predictor_kind=predictor_kind,
            model_version=model_version,
            limit=limit,
        )
        return self._score_uc.execute(request)

    def drift(self, from_version: str, to_version: str) -> DriftReport:
        return self._drift_uc.execute(DriftCitasFeaturesRequest(from_version=from_version, to_version=to_version))

    def export_features(self, dataset_version: str, output_path: str | Path) -> str:
        features = self._feature_store_service.load_citas_features(dataset_version)
        return self._export_features.execute(dataset_version, features, output_path).as_posix()

    def export_metrics(self, train_response: TrainCitasModelResponse, output_path: str | Path) -> str:
        return self._export_metrics.execute(train_response, output_path).as_posix()

    def export_scoring(
        self,
        score_response: ScoreCitasResponse,
        predictor_kind: str,
        model_version: str,
        threshold_used: float,
        output_path: str | Path,
    ) -> str:
        return self._export_scoring.execute(
            score_response,
            predictor_kind=predictor_kind,
            model_version=model_version,
            threshold_used=threshold_used,
            output_path=output_path,
        ).as_posix()

    def export_drift(self, report: DriftReport, output_path: str | Path) -> str:
        return self._export_drift.execute(report, output_path).as_posix()

    def default_baseline_threshold(self) -> float:
        return BaselineCitasPredictor().threshold
