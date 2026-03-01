from __future__ import annotations

import sqlite3
from dataclasses import dataclass
import os
from pathlib import Path

from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.security import Role, UserContext
from clinicdesk.app.application.pipelines.build_citas_dataset import BuildCitasDataset
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.services.prediccion_ausencias_facade import PrediccionAusenciasFacade
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
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_accesos import RepositorioAuditoriaAccesoSqlite
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_medico import AusenciasMedicoRepository
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_personal import AusenciasPersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_calendario_medico import CalendarioMedicoRepository
from clinicdesk.app.infrastructure.sqlite.repos_calendario_personal import CalendarioPersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_dispensaciones import DispensacionesRepository
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import IncidenciasRepository
from clinicdesk.app.infrastructure.sqlite.repos_materiales import MaterialesRepository
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_medicamentos import MedicamentosRepository
from clinicdesk.app.infrastructure.sqlite.repos_movimientos_materiales import MovimientosMaterialesRepository
from clinicdesk.app.infrastructure.sqlite.repos_movimientos_medicamentos import MovimientosMedicamentosRepository
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_recetas import RecetasRepository
from clinicdesk.app.infrastructure.sqlite.repos_salas import SalasRepository
from clinicdesk.app.infrastructure.sqlite.repos_turnos import TurnosRepository
from clinicdesk.app.queries.farmacia_queries import FarmaciaQueries


@dataclass(slots=True)
class QueriesHub:
    farmacia: FarmaciaQueries


@dataclass(slots=True)
class AppContainer:
    connection: sqlite3.Connection
    queries: QueriesHub
    demo_ml_facade: DemoMLFacade
    prediccion_ausencias_facade: PrediccionAusenciasFacade

    pacientes_repo: PacientesRepository
    medicos_repo: MedicosRepository
    personal_repo: PersonalRepository
    salas_repo: SalasRepository
    turnos_repo: TurnosRepository

    calendario_medico_repo: CalendarioMedicoRepository
    calendario_personal_repo: CalendarioPersonalRepository
    ausencias_medico_repo: AusenciasMedicoRepository
    ausencias_personal_repo: AusenciasPersonalRepository

    medicamentos_repo: MedicamentosRepository
    materiales_repo: MaterialesRepository
    mov_medicamentos_repo: MovimientosMedicamentosRepository
    mov_materiales_repo: MovimientosMaterialesRepository

    recetas_repo: RecetasRepository
    dispensaciones_repo: DispensacionesRepository

    citas_repo: CitasRepository
    incidencias_repo: IncidenciasRepository
    auditoria_accesos_repo: RepositorioAuditoriaAccesoSqlite
    user_context: UserContext

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass


def build_container(connection: sqlite3.Connection) -> AppContainer:
    connection.row_factory = sqlite3.Row
    queries = QueriesHub(farmacia=FarmaciaQueries(connection))

    pacientes_repo = PacientesRepository(connection)
    medicos_repo = MedicosRepository(connection)
    personal_repo = PersonalRepository(connection)
    salas_repo = SalasRepository(connection)
    turnos_repo = TurnosRepository(connection)
    calendario_medico_repo = CalendarioMedicoRepository(connection)
    calendario_personal_repo = CalendarioPersonalRepository(connection)
    ausencias_medico_repo = AusenciasMedicoRepository(connection)
    ausencias_personal_repo = AusenciasPersonalRepository(connection)
    medicamentos_repo = MedicamentosRepository(connection)
    materiales_repo = MaterialesRepository(connection)
    mov_medicamentos_repo = MovimientosMedicamentosRepository(connection)
    mov_materiales_repo = MovimientosMaterialesRepository(connection)
    recetas_repo = RecetasRepository(connection)
    dispensaciones_repo = DispensacionesRepository(connection)
    citas_repo = CitasRepository(connection)
    incidencias_repo = IncidenciasRepository(connection)
    auditoria_accesos_repo = RepositorioAuditoriaAccesoSqlite(connection)

    demo_ml_facade = _build_demo_ml_facade(connection, citas_repo, incidencias_repo)
    prediccion_ausencias_facade = _build_prediccion_ausencias_facade(connection)

    role_value = os.getenv("CLINICDESK_ROLE", Role.ADMIN.value).upper()
    role = Role(role_value) if role_value in {r.value for r in Role} else Role.ADMIN
    user_context = UserContext(role=role)

    return AppContainer(
        connection=connection,
        queries=queries,
        demo_ml_facade=demo_ml_facade,
        prediccion_ausencias_facade=prediccion_ausencias_facade,
        pacientes_repo=pacientes_repo,
        medicos_repo=medicos_repo,
        personal_repo=personal_repo,
        salas_repo=salas_repo,
        turnos_repo=turnos_repo,
        calendario_medico_repo=calendario_medico_repo,
        calendario_personal_repo=calendario_personal_repo,
        ausencias_medico_repo=ausencias_medico_repo,
        ausencias_personal_repo=ausencias_personal_repo,
        medicamentos_repo=medicamentos_repo,
        materiales_repo=materiales_repo,
        mov_medicamentos_repo=mov_medicamentos_repo,
        mov_materiales_repo=mov_materiales_repo,
        recetas_repo=recetas_repo,
        dispensaciones_repo=dispensaciones_repo,
        citas_repo=citas_repo,
        incidencias_repo=incidencias_repo,
        auditoria_accesos_repo=auditoria_accesos_repo,
        user_context=user_context,
    )


def _build_demo_ml_facade(
    connection: sqlite3.Connection,
    citas_repo: CitasRepository,
    incidencias_repo: IncidenciasRepository,
) -> DemoMLFacade:
    stores_base = data_dir()
    feature_store_path = Path(stores_base) / "feature_store"
    model_store_path = Path(stores_base) / "model_store"

    feature_service = FeatureStoreService(LocalJsonFeatureStore(feature_store_path))
    model_store = LocalJsonModelStore(model_store_path)
    build_dataset = BuildCitasDataset(SqliteCitasReadAdapter(citas_repo, incidencias_repo))
    return DemoMLFacade(
        read_gateway=SqliteDemoMLReadGateway(connection),
        seed_demo_uc=SeedDemoData(DemoDataSeeder(connection)),
        build_dataset=build_dataset,
        feature_store_service=feature_service,
        train_uc=TrainCitasModel(feature_service, model_store),
        score_uc=ScoreCitas(feature_service, BaselineCitasPredictor(), model_store=model_store),
        drift_uc=DriftCitasFeatures(feature_service),
    )


def _build_prediccion_ausencias_facade(connection: sqlite3.Connection) -> PrediccionAusenciasFacade:
    from clinicdesk.app.application.prediccion_ausencias.usecases import (
        ComprobarDatosPrediccionAusencias,
        EntrenarPrediccionAusencias,
        ObtenerExplicacionRiesgoAusenciaCita,
        PrevisualizarPrediccionAusencias,
    )
    from clinicdesk.app.application.prediccion_ausencias.salud_prediccion import ObtenerSaludPrediccionAusencias
    from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import (
        ObtenerRiesgoAusenciaParaCitas,
    )
    from clinicdesk.app.application.prediccion_ausencias.resultados_recientes import (
        ObtenerResultadosRecientesPrediccionAusencias,
        RegistrarPrediccionesAusenciasAgenda,
    )
    from clinicdesk.app.infrastructure.prediccion_ausencias import (
        AlmacenamientoModeloPrediccion,
        PredictorAusenciasBaseline,
    )
    from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries
    from clinicdesk.app.queries.prediccion_ausencias_resultados_queries import PrediccionAusenciasResultadosQueries

    queries = PrediccionAusenciasQueries(connection)
    resultados_queries = PrediccionAusenciasResultadosQueries(connection)
    almacenamiento = AlmacenamientoModeloPrediccion()
    comprobar_uc = ComprobarDatosPrediccionAusencias(queries, minimo_requerido=50)
    entrenar_uc = EntrenarPrediccionAusencias(
        comprobar_datos_uc=comprobar_uc,
        queries=queries,
        predictor=PredictorAusenciasBaseline(),
        almacenamiento=almacenamiento,
    )
    previsualizar_uc = PrevisualizarPrediccionAusencias(queries, almacenamiento)
    obtener_riesgo_agenda_uc = ObtenerRiesgoAusenciaParaCitas(almacenamiento)
    obtener_explicacion_riesgo_uc = ObtenerExplicacionRiesgoAusenciaCita(queries, almacenamiento)
    obtener_salud_uc = ObtenerSaludPrediccionAusencias(lector_metadata=almacenamiento, queries=queries)
    registrar_predicciones_agenda_uc = RegistrarPrediccionesAusenciasAgenda(resultados_queries)
    obtener_resultados_recientes_uc = ObtenerResultadosRecientesPrediccionAusencias(resultados_queries)
    return PrediccionAusenciasFacade(
        comprobar_uc,
        entrenar_uc,
        previsualizar_uc,
        obtener_riesgo_agenda_uc,
        obtener_explicacion_riesgo_uc,
        obtener_salud_uc,
        registrar_predicciones_agenda_uc,
        obtener_resultados_recientes_uc,
    )
