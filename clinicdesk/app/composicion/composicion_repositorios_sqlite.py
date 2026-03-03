from __future__ import annotations

from dataclasses import dataclass
import sqlite3

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
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite
from clinicdesk.app.infrastructure.sqlite.repos_turnos import TurnosRepository


@dataclass(slots=True)
class RepositoriosSqlite:
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
    telemetria_eventos_repo: RepositorioTelemetriaEventosSqlite


def build_repositorios_sqlite(connection: sqlite3.Connection) -> RepositoriosSqlite:
    return RepositoriosSqlite(
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
        auditoria_accesos_repo=RepositorioAuditoriaAccesoSqlite(connection),
        telemetria_eventos_repo=RepositorioTelemetriaEventosSqlite(connection),
    )
