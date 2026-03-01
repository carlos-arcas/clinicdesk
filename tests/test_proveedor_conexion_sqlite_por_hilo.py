from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

from clinicdesk.app.container import build_container
from clinicdesk.app.infrastructure.sqlite.db import bootstrap
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo


def _crear_db_temporal(db_path: Path) -> sqlite3.Connection:
    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"
    return bootstrap(db_path=db_path, schema_path=schema_path, apply=True)


def _seed_base_tablas(con: sqlite3.Connection) -> tuple[int, int, int]:
    con.execute(
        "INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, activo) VALUES ('DNI', '1', 'Ana', 'Uno', 1)"
    )
    con.execute(
        "INSERT INTO medicos(tipo_documento, documento, nombre, apellidos, activo, num_colegiado, especialidad) VALUES ('DNI', '11', 'Med', 'Uno', 1, 'C1', 'General')"
    )
    con.execute("INSERT INTO salas(nombre, tipo, activa) VALUES ('S1', 'CONSULTA', 1)")
    con.commit()
    return 1, 1, 1


def _insertar_citas_entrenamiento(
    con: sqlite3.Connection,
    *,
    paciente_id: int,
    medico_id: int,
    sala_id: int,
    total: int = 60,
) -> None:
    for idx in range(total):
        inicio = datetime.now() - timedelta(days=120 - idx)
        fin = inicio + timedelta(minutes=30)
        estado = "NO_PRESENTADO" if idx % 4 == 0 else "REALIZADA"
        con.execute(
            """
            INSERT INTO citas(paciente_id, medico_id, sala_id, inicio, fin, estado, activo)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (paciente_id, medico_id, sala_id, inicio.isoformat(), fin.isoformat(), estado),
        )
    con.commit()


def test_proveedor_sqlite_no_comparte_conexion_entre_hilos(tmp_path: Path) -> None:
    db_path = tmp_path / "thread_local.sqlite"
    proveedor = ProveedorConexionSqlitePorHilo(db_path)
    ids: dict[str, int] = {}

    conexion_main = proveedor.obtener()
    ids["main"] = id(conexion_main)

    def ejecutar_en_worker() -> None:
        conexion_worker = proveedor.obtener()
        ids["worker"] = id(conexion_worker)
        proveedor.cerrar_conexion_del_hilo_actual()

    worker = threading.Thread(target=ejecutar_en_worker, name="worker-sqlite")
    worker.start()
    worker.join()

    proveedor.cerrar_conexion_del_hilo_actual()
    assert ids["main"] != ids["worker"]


def test_entrenar_desde_thread_no_rompe_y_actualiza_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "clinicdesk_thread.sqlite"
    conexion_ui = _crear_db_temporal(db_path)
    paciente_id, medico_id, sala_id = _seed_base_tablas(conexion_ui)
    _insertar_citas_entrenamiento(
        conexion_ui,
        paciente_id=paciente_id,
        medico_id=medico_id,
        sala_id=sala_id,
    )
    container = build_container(conexion_ui)
    errores: list[Exception] = []

    def entrenar_en_worker() -> None:
        try:
            container.prediccion_ausencias_facade.entrenar_uc.ejecutar()
        except Exception as exc:  # noqa: BLE001
            errores.append(exc)
        finally:
            container.prediccion_ausencias_facade.proveedor_conexion.cerrar_conexion_del_hilo_actual()

    worker = threading.Thread(target=entrenar_en_worker, name="worker-entrenamiento")
    worker.start()
    worker.join()

    assert not errores
    metadata_path = tmp_path / "data" / "prediccion_ausencias" / "metadata.json"
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["citas_usadas"] == 60

    container.prediccion_ausencias_facade.proveedor_conexion.cerrar_conexion_del_hilo_actual()
    container.close()
