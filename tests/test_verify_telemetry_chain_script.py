from __future__ import annotations

import sqlite3
from pathlib import Path

from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite
from scripts.verify_telemetry_chain import main

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"


def test_verify_telemetry_chain_script_reporta_ok_y_fail(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "telemetry-script.sqlite"
    con = sqlite3.connect(db_path.as_posix())
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    repo = RepositorioTelemetriaEventosSqlite(con)
    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-08T10:00:00+00:00",
            usuario="tester",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto='{"page":"gestion"}',
            entidad_tipo="cita",
            entidad_id="99",
        )
    )

    monkeypatch.setenv("CLINICDESK_DB_PATH", db_path.as_posix())
    assert main() == 0

    con.execute("DROP TRIGGER IF EXISTS trg_telemetria_eventos_no_update")
    con.execute("UPDATE telemetria_eventos SET evento = 'MANIPULADO' WHERE id = 1")
    con.commit()

    assert main() == 1


def test_verify_telemetry_chain_script_legacy_se_migra_en_verificacion_y_luego_detecta_tampering(
    tmp_path: Path, monkeypatch
) -> None:
    db_path = tmp_path / "telemetry-script-legacy.sqlite"
    con = sqlite3.connect(db_path.as_posix())
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE telemetria_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            usuario TEXT NOT NULL,
            modo_demo INTEGER NOT NULL,
            evento TEXT NOT NULL,
            contexto TEXT,
            entidad_tipo TEXT,
            entidad_id TEXT
        );
        INSERT INTO telemetria_eventos(timestamp_utc, usuario, modo_demo, evento, contexto, entidad_tipo, entidad_id)
        VALUES ('2026-01-08T10:00:00+00:00', 'legacy', 0, 'evento_legacy', '{"page":"legacy"}', 'cita', '7');
        """
    )
    con.commit()

    monkeypatch.setenv("CLINICDESK_DB_PATH", db_path.as_posix())
    assert main() == 0

    repo = RepositorioTelemetriaEventosSqlite(con)
    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-08T10:01:00+00:00",
            usuario="nuevo",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto='{"page":"gestion"}',
            entidad_tipo="cita",
            entidad_id="8",
        )
    )

    assert main() == 0

    con.execute("DROP TRIGGER IF EXISTS trg_telemetria_eventos_no_update")
    con.execute("UPDATE telemetria_eventos SET evento = 'manipulado' WHERE id = 2")
    con.commit()

    assert main() == 1
