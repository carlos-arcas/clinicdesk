from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_salas import SalasRepository
from clinicdesk.app.infrastructure.sqlite.repos_turnos import TurnosRepository

from clinicdesk.app.infrastructure.sqlite.repos_calendario_medico import CalendarioMedicoRepository
from clinicdesk.app.infrastructure.sqlite.repos_calendario_personal import CalendarioPersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_medico import AusenciasMedicoRepository
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_personal import AusenciasPersonalRepository

from clinicdesk.app.infrastructure.sqlite.repos_medicamentos import MedicamentosRepository
from clinicdesk.app.infrastructure.sqlite.repos_materiales import MaterialesRepository

from clinicdesk.app.infrastructure.sqlite.repos_recetas import RecetasRepository
from clinicdesk.app.infrastructure.sqlite.repos_dispensaciones import DispensacionesRepository

from clinicdesk.app.infrastructure.sqlite.repos_movimientos_medicamentos import MovimientosMedicamentosRepository
from clinicdesk.app.infrastructure.sqlite.repos_movimientos_materiales import MovimientosMaterialesRepository

from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import IncidenciasRepository

# ✅ Queries (lecturas para UI)
from clinicdesk.app.queries.farmacia_queries import FarmaciaQueries


@dataclass(slots=True)
class QueriesHub:
    """Agrupador de queries (solo SELECT) para la UI."""
    farmacia: FarmaciaQueries
    # En fase 2: citas: CitasQueries, incidencias: IncidenciasQueries, etc.


@dataclass(slots=True)
class AppContainer:
    """Contenedor de dependencias de la aplicación."""

    connection: sqlite3.Connection
    queries: QueriesHub

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

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass


def build_container(connection: sqlite3.Connection) -> AppContainer:
    """Construye el container con repositorios y queries."""

    # ✅ Imprescindible para que las queries puedan usar row["col"]
    connection.row_factory = sqlite3.Row

    queries = QueriesHub(
        farmacia=FarmaciaQueries(connection),
    )

    return AppContainer(
        connection=connection,
        queries=queries,
        pacientes_repo=PacientesRepository(connection),
        medicos_repo=MedicosRepository(connection),
        personal_repo=PersonalRepository(connection),
        salas_repo=SalasRepository(connection),
        turnos_repo=TurnosRepository(connection),
        calendario_medico_repo=CalendarioMedicoRepository(connection),
        calendario_personal_repo=CalendarioPersonalRepository(connection),
        ausencias_medico_repo=AusenciasMedicoRepository(connection),
        ausencias_personal_repo=AusenciasPersonalRepository(connection),
        medicamentos_repo=MedicamentosRepository(connection),
        materiales_repo=MaterialesRepository(connection),
        mov_medicamentos_repo=MovimientosMedicamentosRepository(connection),
        mov_materiales_repo=MovimientosMaterialesRepository(connection),
        recetas_repo=RecetasRepository(connection),
        dispensaciones_repo=DispensacionesRepository(connection),
        citas_repo=CitasRepository(connection),
        incidencias_repo=IncidenciasRepository(connection),
    )
