from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Any

from clinicdesk.app.application.security import Role, UserContext
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.prediccion_ausencias_facade import PrediccionAusenciasFacade
from clinicdesk.app.application.services.prediccion_operativa_facade import PrediccionOperativaFacade
from clinicdesk.app.application.services.recordatorios_citas_facade import RecordatoriosCitasFacade
from clinicdesk.app.composicion.composicion_demo_ml import build_demo_ml_facade
from clinicdesk.app.composicion.composicion_prediccion_ausencias import build_prediccion_ausencias_facade
from clinicdesk.app.composicion.composicion_prediccion_operativa import build_prediccion_operativa_facade
from clinicdesk.app.composicion.composicion_proveedores import build_proveedor_conexion_sqlite_por_hilo
from clinicdesk.app.composicion.composicion_queries import build_farmacia_queries
from clinicdesk.app.composicion.composicion_recordatorios import build_recordatorios_citas_facade
from clinicdesk.app.composicion.composicion_repositorios_sqlite import build_repositorios_sqlite
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
    recordatorios_citas_facade: RecordatoriosCitasFacade
    prediccion_operativa_facade: PrediccionOperativaFacade

    pacientes_repo: Any
    medicos_repo: Any
    personal_repo: Any
    salas_repo: Any
    turnos_repo: Any

    calendario_medico_repo: Any
    calendario_personal_repo: Any
    ausencias_medico_repo: Any
    ausencias_personal_repo: Any

    medicamentos_repo: Any
    materiales_repo: Any
    mov_medicamentos_repo: Any
    mov_materiales_repo: Any

    recetas_repo: Any
    dispensaciones_repo: Any

    citas_repo: Any
    incidencias_repo: Any
    auditoria_accesos_repo: Any
    telemetria_eventos_repo: Any
    user_context: UserContext

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass


def build_container(connection: sqlite3.Connection) -> AppContainer:
    connection.row_factory = sqlite3.Row
    repos = build_repositorios_sqlite(connection)
    proveedor_prediccion = build_proveedor_conexion_sqlite_por_hilo(connection)
    proveedor_recordatorios = build_proveedor_conexion_sqlite_por_hilo(connection)
    return AppContainer(
        connection=connection,
        queries=QueriesHub(farmacia=build_farmacia_queries(connection)),
        demo_ml_facade=build_demo_ml_facade(connection, repos.citas_repo, repos.incidencias_repo),
        prediccion_ausencias_facade=build_prediccion_ausencias_facade(proveedor_prediccion),
        recordatorios_citas_facade=build_recordatorios_citas_facade(proveedor_recordatorios),
        prediccion_operativa_facade=build_prediccion_operativa_facade(proveedor_prediccion),
        pacientes_repo=repos.pacientes_repo,
        medicos_repo=repos.medicos_repo,
        personal_repo=repos.personal_repo,
        salas_repo=repos.salas_repo,
        turnos_repo=repos.turnos_repo,
        calendario_medico_repo=repos.calendario_medico_repo,
        calendario_personal_repo=repos.calendario_personal_repo,
        ausencias_medico_repo=repos.ausencias_medico_repo,
        ausencias_personal_repo=repos.ausencias_personal_repo,
        medicamentos_repo=repos.medicamentos_repo,
        materiales_repo=repos.materiales_repo,
        mov_medicamentos_repo=repos.mov_medicamentos_repo,
        mov_materiales_repo=repos.mov_materiales_repo,
        recetas_repo=repos.recetas_repo,
        dispensaciones_repo=repos.dispensaciones_repo,
        citas_repo=repos.citas_repo,
        incidencias_repo=repos.incidencias_repo,
        auditoria_accesos_repo=repos.auditoria_accesos_repo,
        telemetria_eventos_repo=repos.telemetria_eventos_repo,
        user_context=build_user_context(),
    )


def build_user_context() -> UserContext:
    role_value = os.getenv("CLINICDESK_ROLE", Role.ADMIN.value).upper()
    role = Role(role_value) if role_value in {valor.value for valor in Role} else Role.ADMIN
    return UserContext(role=role)
