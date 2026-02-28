from __future__ import annotations

from pathlib import Path

import pytest

from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.infrastructure.sqlite.reset_safety import (
    UnsafeDatabaseResetError,
    build_reset_confirmation_help,
    evaluate_reset_safety,
    reset_demo_database,
)


def test_reset_demo_database_allows_safe_path_and_recreates_db(tmp_path) -> None:
    safe_data_dir = Path.cwd() / "data"
    safe_data_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = safe_data_dir / f"demo-reset-{tmp_path.name}.db"

    connection = bootstrap_database(apply_schema=True, sqlite_path=sqlite_path.as_posix())
    connection.execute(
        "INSERT INTO medicos (tipo_documento, documento, nombre, apellidos, telefono, email, fecha_nacimiento, direccion, activo, num_colegiado, especialidad) "
        "VALUES ('DNI', '12345678A', 'Demo', 'Doctor', '600123123', 'demo@example.com', '1980-01-01', 'Calle Demo', 1, 'COL123', 'Medicina General')"
    )
    connection.commit()
    connection.close()

    reset_demo_database(sqlite_path)

    check_connection = bootstrap_database(apply_schema=True, sqlite_path=sqlite_path.as_posix())
    try:
        row = check_connection.execute("SELECT COUNT(*) FROM medicos").fetchone()
    finally:
        check_connection.close()
        sqlite_path.unlink(missing_ok=True)
    assert row is not None
    assert int(row[0]) == 0


def test_reset_demo_database_blocks_unsafe_path(tmp_path) -> None:
    unsafe_path = tmp_path / "other" / "real.db"
    unsafe_path.parent.mkdir(parents=True, exist_ok=True)
    unsafe_path.write_text("placeholder", encoding="utf-8")

    with pytest.raises(UnsafeDatabaseResetError):
        reset_demo_database(unsafe_path)


def test_reset_demo_database_requires_strong_confirmation_for_demo_name_outside_data(tmp_path) -> None:
    suspicious_path = tmp_path / "demo-like.db"
    suspicious_path.write_text("placeholder", encoding="utf-8")

    safety = evaluate_reset_safety(suspicious_path)
    assert safety.is_allowed is True
    assert safety.requires_strong_confirmation is True
    assert safety.reason_code == "safe_by_demo_name_only"

    with pytest.raises(UnsafeDatabaseResetError, match="missing_strong_confirmation"):
        reset_demo_database(suspicious_path)


def test_reset_demo_database_accepts_strong_confirmation_for_suspicious_path(tmp_path) -> None:
    suspicious_path = tmp_path / "demo-force.db"
    suspicious_path.write_text("placeholder", encoding="utf-8")

    confirmation = build_reset_confirmation_help(suspicious_path)
    reset_demo_database(suspicious_path, confirmation_token=confirmation)

    assert suspicious_path.exists()
