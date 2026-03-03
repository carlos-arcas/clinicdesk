from __future__ import annotations

import sqlite3
import threading

from clinicdesk.app.infrastructure.sqlite.sqlite_connection_config import configurar_conexion


def test_configurar_conexion_concurrente_no_lanza_bloqueo(tmp_path) -> None:
    db_path = tmp_path / "concurrente.sqlite"
    sqlite3.connect(db_path).close()

    errores: list[Exception] = []
    errores_lock = threading.Lock()

    def _configurar() -> None:
        con = sqlite3.connect(db_path)
        try:
            configurar_conexion(con, db_path)
        except Exception as exc:  # pragma: no cover
            with errores_lock:
                errores.append(exc)
        finally:
            con.close()

    hilos = [threading.Thread(target=_configurar) for _ in range(6)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert not errores
