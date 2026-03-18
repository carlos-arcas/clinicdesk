from __future__ import annotations

import sqlite3
from pathlib import Path

from clinicdesk.app.application.auditoria.audit_service import AuditService
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.pipelines.build_citas_dataset import BuildCitasDataset
from clinicdesk.app.application.security import AutorizadorAcciones, UserContext
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.services.seguimiento_operativo_ml_service import SeguimientoOperativoMLService
from clinicdesk.app.application.usecases.drift_citas_features import DriftCitasFeatures
from clinicdesk.app.application.usecases.score_citas import ScoreCitas
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModel
from clinicdesk.app.bootstrap import data_dir
from clinicdesk.app.infrastructure.feature_store.local_json_feature_store import LocalJsonFeatureStore
from clinicdesk.app.infrastructure.model_store.local_json_model_store import LocalJsonModelStore
from clinicdesk.app.infrastructure.sqlite.citas_read_adapter import SqliteCitasReadAdapter
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder
from clinicdesk.app.infrastructure.sqlite.demo_ml_read_gateway import SqliteDemoMLReadGateway
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_eventos import RepositorioAuditoriaEventosSqlite
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import IncidenciasRepository
from clinicdesk.app.infrastructure.sqlite.repos_seguimiento_operativo_ml import RepositorioSeguimientoOperativoMLSqlite


def build_analitica_ml_facade(
    connection: sqlite3.Connection,
    citas_repo: CitasRepository,
    incidencias_repo: IncidenciasRepository,
    *,
    user_context: UserContext,
    autorizador_acciones: AutorizadorAcciones,
) -> DemoMLFacade:
    stores_base = data_dir()
    feature_store_path = Path(stores_base) / "feature_store"
    model_store_path = Path(stores_base) / "model_store"
    feature_service = FeatureStoreService(LocalJsonFeatureStore(feature_store_path))
    model_store = LocalJsonModelStore(model_store_path)
    dataset_uc = BuildCitasDataset(SqliteCitasReadAdapter(citas_repo, incidencias_repo))
    seguimiento_operativo = SeguimientoOperativoMLService(RepositorioSeguimientoOperativoMLSqlite(connection))
    return DemoMLFacade(
        read_gateway=SqliteDemoMLReadGateway(connection),
        seed_demo_uc=SeedDemoData(
            DemoDataSeeder(connection),
            user_context=user_context,
            autorizador_acciones=autorizador_acciones,
            audit_service=AuditService(repository=build_repositorio_auditoria_eventos(connection)),
        ),
        build_dataset=dataset_uc,
        feature_store_service=feature_service,
        train_uc=TrainCitasModel(feature_service, model_store),
        score_uc=ScoreCitas(feature_service, BaselineCitasPredictor(), model_store=model_store),
        drift_uc=DriftCitasFeatures(feature_service),
        model_store=model_store,
        seguimiento_operativo_service=seguimiento_operativo,
    )


def build_demo_ml_facade(
    connection: sqlite3.Connection,
    citas_repo: CitasRepository,
    incidencias_repo: IncidenciasRepository,
    *,
    user_context: UserContext,
    autorizador_acciones: AutorizadorAcciones,
) -> DemoMLFacade:
    """Alias legacy estable mientras existan imports internos con naming histórico."""
    return build_analitica_ml_facade(
        connection,
        citas_repo,
        incidencias_repo,
        user_context=user_context,
        autorizador_acciones=autorizador_acciones,
    )


def build_repositorio_auditoria_eventos(connection: sqlite3.Connection) -> RepositorioAuditoriaEventosSqlite:
    return RepositorioAuditoriaEventosSqlite(connection)
