from __future__ import annotations

import sqlite3

from clinicdesk.app.queries.prediccion_operativa_queries import PrediccionOperativaQueries


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE citas (
          id INTEGER PRIMARY KEY,
          activo INTEGER,
          estado TEXT,
          inicio TEXT,
          medico_id INTEGER,
          tipo_cita TEXT,
          check_in_at TEXT,
          llamado_a_consulta_at TEXT,
          consulta_inicio_at TEXT,
          consulta_fin_at TEXT
        )
        """
    )
    return con


def test_datasets_operativos_filtran_hitos_validos():
    con = _con()
    con.execute(
        "INSERT INTO citas VALUES (1,1,'REALIZADA','2026-01-10 09:00:00',4,'CONTROL','2026-01-10 08:50:00','2026-01-10 09:05:00','2026-01-10 09:07:00','2026-01-10 09:25:00')"
    )
    con.execute(
        "INSERT INTO citas VALUES (2,1,'REALIZADA','2026-01-10 10:00:00',4,'CONTROL',NULL,NULL,'2026-01-10 10:10:00','2026-01-10 10:00:00')"
    )
    queries = PrediccionOperativaQueries(con)

    duraciones = queries.obtener_dataset_duracion("2026-01-01 00:00:00", "2026-01-31 23:59:59")
    esperas = queries.obtener_dataset_espera("2026-01-01 00:00:00", "2026-01-31 23:59:59")

    assert len(duraciones) == 1
    assert len(esperas) == 1
    assert round(duraciones[0].duracion_min) == 18
    assert round(esperas[0].espera_min) == 15


def test_proximas_citas_para_prediccion():
    con = _con()
    con.execute(
        "INSERT INTO citas VALUES (11,1,'PROGRAMADA','2030-01-10 17:00:00',8,'PRIMERA_VISITA',NULL,NULL,NULL,NULL)"
    )
    queries = PrediccionOperativaQueries(con)
    rows = queries.obtener_proximas_citas_para_prediccion("2030-01-01 00:00:00", "2030-01-31 23:59:59")
    assert rows[0].cita_id == 11
    assert rows[0].franja_hora == "16-20"
