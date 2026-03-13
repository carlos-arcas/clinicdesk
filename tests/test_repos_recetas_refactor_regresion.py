from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Medico, Paciente, Receta
from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.recetas.consultas import construir_consulta_por_actor
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_recetas import RecetasRepository


def _schema_path() -> Path:
    return Path("clinicdesk/app/infrastructure/sqlite/schema.sql").resolve()


def test_construir_consulta_por_actor_compone_sql_y_parametros() -> None:
    sql, params = construir_consulta_por_actor(
        campo_actor="medico",
        actor_id=5,
        desde="2025-01-01 00:00:00",
        hasta="2025-12-31 23:59:59",
    )

    assert "medico_id = ?" in sql
    assert "activo = 1" in sql
    assert params == [5, "2025-01-01 00:00:00", "2025-12-31 23:59:59"]


def test_construir_consulta_por_actor_valida_id() -> None:
    with pytest.raises(ValidationError, match="paciente_id inválido"):
        construir_consulta_por_actor(campo_actor="paciente", actor_id=0, desde=None, hasta=None)


def test_repo_recetas_filtra_por_rango_sin_regresion(tmp_path: Path) -> None:
    con = db.bootstrap(tmp_path / "recetas.sqlite", _schema_path(), apply=True)
    paciente_id = PacientesRepository(con).create(
        Paciente(
            tipo_documento=TipoDocumento.DNI,
            documento="11222333A",
            nombre="Sara",
            apellidos="Lopez",
            fecha_nacimiento=date(1990, 1, 2),
        )
    )
    medico_id = MedicosRepository(con).create(
        Medico(
            tipo_documento=TipoDocumento.DNI,
            documento="44555666B",
            nombre="Mario",
            apellidos="Diaz",
            fecha_nacimiento=date(1985, 6, 7),
            num_colegiado="COL-123",
            especialidad="General",
        )
    )

    repo = RecetasRepository(con)
    base = datetime(2025, 1, 15, 9, 0, 0)
    receta_antigua = repo.create_receta(
        Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=base - timedelta(days=10))
    )
    receta_nueva = repo.create_receta(Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=base))

    recetas = repo.list_recetas_by_paciente(
        paciente_id,
        desde="2025-01-01 00:00:00",
        hasta="2025-01-20 23:59:59",
    )

    assert [receta.id for receta in recetas] == [receta_nueva, receta_antigua]
    con.close()
