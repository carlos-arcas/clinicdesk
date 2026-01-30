from __future__ import annotations

import difflib
import pprint
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

import pytest

from clinicdesk.app.container import build_container
from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import (
    Medicamento,
    Material,
    Medico,
    Paciente,
    Personal,
    Receta,
    RecetaLinea,
    Sala,
)
from clinicdesk.app.infrastructure.sqlite.repos_calendario_medico import (
    BloqueCalendarioMedico,
)
from clinicdesk.app.infrastructure.sqlite.repos_turnos import Turno


TEST_DB_PATH = Path(__file__).resolve().parent / "tmp" / "clinicdesk_test.sqlite"


def _apply_pragmas(con: sqlite3.Connection) -> None:
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    con.execute("PRAGMA temp_store = MEMORY;")
    con.execute("PRAGMA busy_timeout = 5000;")


def _apply_schema(con: sqlite3.Connection) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    con.executescript(sql)
    con.commit()


def _ensure_column(con: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    columns = {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
    if column in columns:
        return
    con.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
    con.commit()


def _ensure_test_migrations(con: sqlite3.Connection) -> None:
    _ensure_column(
        con,
        "dispensaciones",
        "incidencia",
        "incidencia INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(
        con,
        "dispensaciones",
        "notas_incidencia",
        "notas_incidencia TEXT",
    )


@pytest.fixture()
def db_connection() -> sqlite3.Connection:
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{TEST_DB_PATH}{suffix}")
        if path.exists():
            path.unlink()

    con = sqlite3.connect(TEST_DB_PATH.as_posix())
    con.row_factory = sqlite3.Row
    _apply_pragmas(con)
    _apply_schema(con)
    _ensure_test_migrations(con)

    try:
        yield con
    finally:
        try:
            con.close()
        finally:
            for suffix in ("", "-wal", "-shm"):
                path = Path(f"{TEST_DB_PATH}{suffix}")
                if path.exists():
                    path.unlink()


@pytest.fixture()
def container(db_connection: sqlite3.Connection):
    return build_container(db_connection)


@pytest.fixture()
def assert_expected_actual():
    def _assert(expected: Any, actual: Any, *, message: str) -> None:
        expected_str = pprint.pformat(expected, width=120)
        actual_str = pprint.pformat(actual, width=120)
        diff = "\n".join(
            difflib.unified_diff(
                expected_str.splitlines(),
                actual_str.splitlines(),
                fromfile="expected",
                tofile="actual",
                lineterm="",
            )
        )
        assert expected == actual, (
            f"{message}\nExpected:\n{expected_str}\nActual:\n{actual_str}\nDiff:\n{diff}"
        )

    return _assert


@pytest.fixture()
def seed_data(container) -> Dict[str, Any]:
    pacientes_repo = container.pacientes_repo
    medicos_repo = container.medicos_repo
    personal_repo = container.personal_repo
    salas_repo = container.salas_repo
    turnos_repo = container.turnos_repo
    calendario_repo = container.calendario_medico_repo
    medicamentos_repo = container.medicamentos_repo
    materiales_repo = container.materiales_repo
    recetas_repo = container.recetas_repo

    paciente_activo = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="12345678",
        nombre="Laura",
        apellidos="Gomez",
        telefono="600123456",
        email=None,
        fecha_nacimiento=date(1990, 5, 12),
        direccion="Calle Salud 123",
        activo=True,
        num_historia="H-100",
        alergias=None,
        observaciones=None,
    )
    paciente_inactivo = Paciente(
        tipo_documento=TipoDocumento.NIE,
        documento="X1234567",
        nombre="Mario",
        apellidos="Perez",
        telefono=None,
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=False,
        num_historia=None,
        alergias=None,
        observaciones=None,
    )

    paciente_activo_id = pacientes_repo.create(paciente_activo)
    paciente_inactivo_id = pacientes_repo.create(paciente_inactivo)

    medico_activo = Medico(
        tipo_documento=TipoDocumento.DNI,
        documento="87654321",
        nombre="Elena",
        apellidos="Martinez",
        telefono="611222333",
        email="elena@clinic.test",
        fecha_nacimiento=date(1985, 3, 20),
        direccion="Avenida Medica 1",
        activo=True,
        num_colegiado="MED-100",
        especialidad="Pediatria",
    )
    medico_inactivo = Medico(
        tipo_documento=TipoDocumento.PASAPORTE,
        documento="P1234567",
        nombre="Luis",
        apellidos="Ruiz",
        telefono="622333444",
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=False,
        num_colegiado="MED-200",
        especialidad="Traumatologia",
    )

    medico_activo_id = medicos_repo.create(medico_activo)
    medico_inactivo_id = medicos_repo.create(medico_inactivo)

    personal_activo = Personal(
        tipo_documento=TipoDocumento.DNI,
        documento="11223344",
        nombre="Carla",
        apellidos="Lopez",
        telefono="633444555",
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=True,
        puesto="Enfermeria",
        turno="Mañana",
    )
    personal_inactivo = Personal(
        tipo_documento=TipoDocumento.DNI,
        documento="99887766",
        nombre="Raul",
        apellidos="Diaz",
        telefono=None,
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=False,
        puesto="Administracion",
        turno=None,
    )

    personal_activo_id = personal_repo.create(personal_activo)
    personal_inactivo_id = personal_repo.create(personal_inactivo)

    sala_activa = Sala(
        nombre="Consulta 1",
        tipo=TipoSala.CONSULTA,
        ubicacion="Planta 1",
        activa=True,
    )
    sala_inactiva = Sala(
        nombre="RX 1",
        tipo=TipoSala.RX,
        ubicacion=None,
        activa=False,
    )

    sala_activa_id = salas_repo.create(sala_activa)
    sala_inactiva_id = salas_repo.create(sala_inactiva)

    turno_id = turnos_repo.create(
        Turno(
            nombre="Turno mañana",
            hora_inicio="08:00",
            hora_fin="14:00",
            activo=True,
        )
    )

    calendario_repo.create(
        BloqueCalendarioMedico(
            medico_id=medico_activo_id,
            fecha="2024-05-20",
            turno_id=turno_id,
            hora_inicio_override=None,
            hora_fin_override=None,
            observaciones=None,
            activo=True,
        )
    )

    medicamento_activo = Medicamento(
        nombre_compuesto="Amoxicilina",
        nombre_comercial="Amoxil",
        cantidad_almacen=20,
        activo=True,
    )
    medicamento_inactivo = Medicamento(
        nombre_compuesto="Ibuprofeno",
        nombre_comercial="Ibupro",
        cantidad_almacen=0,
        activo=False,
    )

    medicamento_activo_id = medicamentos_repo.create(medicamento_activo)
    medicamento_inactivo_id = medicamentos_repo.create(medicamento_inactivo)

    material_activo = Material(
        nombre="Guantes nitrilo",
        fungible=True,
        cantidad_almacen=100,
        activo=True,
    )
    material_inactivo = Material(
        nombre="Monitor ECG",
        fungible=False,
        cantidad_almacen=2,
        activo=False,
    )

    material_activo_id = materiales_repo.create(material_activo)
    material_inactivo_id = materiales_repo.create(material_inactivo)

    receta_id = recetas_repo.create_receta(
        Receta(
            paciente_id=paciente_activo_id,
            medico_id=medico_activo_id,
            fecha=datetime(2024, 5, 20, 9, 0, 0),
            observaciones="Receta inicial",
        )
    )

    receta_linea_id = recetas_repo.add_linea(
        RecetaLinea(
            receta_id=receta_id,
            medicamento_id=medicamento_activo_id,
            dosis="1 cada 8h",
            duracion_dias=7,
            instrucciones=None,
        )
    )

    return {
        "paciente_activo_id": paciente_activo_id,
        "paciente_inactivo_id": paciente_inactivo_id,
        "medico_activo_id": medico_activo_id,
        "medico_inactivo_id": medico_inactivo_id,
        "personal_activo_id": personal_activo_id,
        "personal_inactivo_id": personal_inactivo_id,
        "sala_activa_id": sala_activa_id,
        "sala_inactiva_id": sala_inactiva_id,
        "turno_id": turno_id,
        "medicamento_activo_id": medicamento_activo_id,
        "medicamento_inactivo_id": medicamento_inactivo_id,
        "material_activo_id": material_activo_id,
        "material_inactivo_id": material_inactivo_id,
        "receta_id": receta_id,
        "receta_linea_id": receta_linea_id,
    }
