from __future__ import annotations

import sqlite3

from clinicdesk.app.application.services.seguimiento_operativo_ml_service import (
    AccionHumanaItemML,
    EstadoSeguimientoItemML,
    HistorialDecisionML,
)
from clinicdesk.app.infrastructure.sqlite.repos_seguimiento_operativo_ml import RepositorioSeguimientoOperativoMLSqlite


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE ml_acciones_operativas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cita_id TEXT NOT NULL,
            prioridad_ml TEXT NOT NULL,
            accion_sugerida_ml TEXT NOT NULL,
            accion_humana TEXT NOT NULL,
            estado TEXT NOT NULL,
            nota_corta TEXT NOT NULL DEFAULT '',
            timestamp_utc TEXT NOT NULL,
            actor TEXT NOT NULL DEFAULT 'operador'
        );
        """
    )
    return con


def test_repositorio_persiste_y_lista_historial() -> None:
    repo = RepositorioSeguimientoOperativoMLSqlite(_con())
    repo.registrar_decision(
        HistorialDecisionML(
            cita_id="33",
            prioridad_ml="alta",
            accion_sugerida_ml="confirmar_hoy",
            accion_humana=AccionHumanaItemML.ABRIR_CITA,
            estado=EstadoSeguimientoItemML.REVISADO,
            nota_corta="ok",
            timestamp_utc="2026-01-01T10:00:00+00:00",
            actor="staff",
        )
    )

    historial = repo.obtener_historial("33")

    assert len(historial) == 1
    assert historial[0].estado == EstadoSeguimientoItemML.REVISADO
    assert historial[0].accion_humana == AccionHumanaItemML.ABRIR_CITA
