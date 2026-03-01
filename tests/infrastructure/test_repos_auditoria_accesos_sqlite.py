from __future__ import annotations

from clinicdesk.app.application.auditoria_acceso import (
    AccionAuditoriaAcceso,
    EntidadAuditoriaAcceso,
    EventoAuditoriaAcceso,
)
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
