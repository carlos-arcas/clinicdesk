from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository


def _schema_path() -> Path:
    return Path("clinicdesk/app/infrastructure/sqlite/schema.sql").resolve()


def _build_paciente(documento: str = "12345678") -> Paciente:
    return Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento=documento,
        nombre="Ana",
        apellidos="Paredes",
        telefono="600999888",
        email="ana@clinic.test",
        fecha_nacimiento=date(1992, 1, 2),
        direccion="Calle Secreta 123",
        activo=True,
        num_historia=None,
        alergias="penicilina",
        observaciones="nota sensible",
    )


def test_encrypts_pii_and_decrypts_on_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "true")
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_KEY", "test-key-material")

    db_path = tmp_path / "pii.sqlite"
    con = db.bootstrap(db_path, _schema_path(), apply=True)
    repo = PacientesRepository(con)

    paciente_id = repo.create(_build_paciente())
    stored = con.execute(
        "SELECT telefono, email, direccion, alergias, observaciones FROM pacientes WHERE id = ?",
        (paciente_id,),
    ).fetchone()

    for column in ("telefono", "email", "direccion", "alergias", "observaciones"):
        assert str(stored[column]).startswith("enc:v1:")

    read_back = repo.get_by_id(paciente_id)
    assert read_back is not None
    assert read_back.telefono == "600999888"
    assert read_back.email == "ana@clinic.test"
    assert read_back.direccion == "Calle Secreta 123"
    assert read_back.alergias == "penicilina"
    assert read_back.observaciones == "nota sensible"

    con.execute("PRAGMA wal_checkpoint(FULL);")
    con.close()

    all_bytes = b""
    for suffix in ("", "-wal", "-shm"):
        file_path = Path(f"{db_path}{suffix}")
        if file_path.exists():
            all_bytes += file_path.read_bytes()
    assert b"600999888" not in all_bytes
    assert b"ana@clinic.test" not in all_bytes


def test_requires_key_when_encryption_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "1")
    monkeypatch.delenv("CLINICDESK_PII_ENCRYPTION_KEY", raising=False)

    with pytest.raises(RuntimeError, match="CLINICDESK_PII_ENCRYPTION_KEY"):
        db.bootstrap(tmp_path / "missing-key.sqlite", _schema_path(), apply=True)


def test_migrates_legacy_plaintext_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "legacy.sqlite"

    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.delenv("CLINICDESK_PII_ENCRYPTION_KEY", raising=False)
    legacy_con = db.bootstrap(db_path, _schema_path(), apply=True)
    legacy_repo = PacientesRepository(legacy_con)
    paciente_id = legacy_repo.create(_build_paciente(documento="87654321"))
    legacy_con.close()

    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "true")
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_KEY", "migration-key")

    secured_con = db.bootstrap(db_path, _schema_path(), apply=True)
    migrated = secured_con.execute(
        "SELECT telefono, email FROM pacientes WHERE id = ?",
        (paciente_id,),
    ).fetchone()
    assert str(migrated["telefono"]).startswith("enc:v1:")
    assert str(migrated["email"]).startswith("enc:v1:")

    secured_repo = PacientesRepository(secured_con)
    read_back = secured_repo.get_by_id(paciente_id)
    assert read_back is not None
    assert read_back.telefono == "600999888"
    assert read_back.email == "ana@clinic.test"
