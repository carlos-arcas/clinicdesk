from __future__ import annotations

import json

from clinicdesk.app.application.auditoria_acceso import (
    AccionAuditoriaAcceso,
    EntidadAuditoriaAcceso,
    EventoAuditoriaAcceso,
)
from clinicdesk.app.application.security import Role, UserContext
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import RegistrarAuditoriaAcceso
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_accesos import RepositorioAuditoriaAccesoSqlite


def test_repositorio_auditoria_acceso_sqlite_inserta_evento(db_connection) -> None:
    repo = RepositorioAuditoriaAccesoSqlite(db_connection)
    evento = EventoAuditoriaAcceso(
        timestamp_utc="2026-01-01T10:11:12+00:00",
        usuario="admin",
        modo_demo=False,
        accion=AccionAuditoriaAcceso.VER_DETALLE_CITA,
        entidad_tipo=EntidadAuditoriaAcceso.CITA,
        entidad_id="15",
    )

    repo.registrar(evento)

    row = db_connection.execute(
        """
        SELECT usuario, modo_demo, accion, entidad_tipo, entidad_id
        FROM auditoria_accesos
        WHERE entidad_id = ?
        """,
        ("15",),
    ).fetchone()

    assert row is not None
    assert row["usuario"] == "admin"
    assert row["modo_demo"] == 0
    assert row["accion"] == AccionAuditoriaAcceso.VER_DETALLE_CITA.value
    assert row["entidad_tipo"] == EntidadAuditoriaAcceso.CITA.value


def test_usecase_y_repo_no_persisten_pii_en_metadata_json(db_connection) -> None:
    repo = RepositorioAuditoriaAccesoSqlite(db_connection)
    usecase = RegistrarAuditoriaAcceso(repo)
    contexto = UserContext(role=Role.ADMIN, username="auditor", demo_mode=False)

    usecase.execute(
        contexto_usuario=contexto,
        accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
        entidad_tipo=EntidadAuditoriaAcceso.PACIENTE,
        entidad_id=77,
        metadata={
            "origen": "pacientes",
            "contexto": {
                "email": "ana@test.com",
                "detalle": "dni=12345678Z telefono=600123123",
            },
        },
    )

    row = db_connection.execute(
        """
        SELECT metadata_json
        FROM auditoria_accesos
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    assert row is not None
    metadata = json.loads(row["metadata_json"] or "{}")
    assert metadata["origen"] == "pacientes"
    assert "email" not in metadata["contexto"]
    assert "12345678Z" not in metadata["contexto"]["detalle"]
    assert "600123123" not in metadata["contexto"]["detalle"]
    assert metadata["redaccion_aplicada"] is True
