from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

try:
    import cryptography  # noqa: F401
except ImportError as exc:  # pragma: no cover - depende del entorno
    raise RuntimeError(
        "La dependencia obligatoria 'cryptography' no está instalada. "
        "Instálala con: pip install cryptography"
    ) from exc

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Medico
from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from scripts.crypto_migrate_medicos import (
    MigrationOptions,
    _migrate,
    _validate_options,
)


def _schema_path() -> Path:
    return Path("clinicdesk/app/infrastructure/sqlite/schema.sql").resolve()


def _legacy_medico() -> Medico:
    return Medico(
        tipo_documento=TipoDocumento.DNI,
        documento="87654321",
        nombre="Mario",
        apellidos="Sanz",
        telefono="611222333",
        email="mario@clinic.test",
        fecha_nacimiento=date(1980, 8, 20),
        direccion="Avenida Sur 9",
        activo=True,
        num_colegiado="COL-777",
        especialidad="Pediatría",
    )


def test_backfill_migrates_legacy_medico_and_can_wipe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "medicos.sqlite"

    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "0")
    monkeypatch.delenv("CLINICDESK_CRYPTO_KEY", raising=False)
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.delenv("CLINICDESK_PII_ENCRYPTION_KEY", raising=False)

    con = db.bootstrap(db_path, _schema_path(), apply=True)
    repo = MedicosRepository(con)
    medico_id = repo.create(_legacy_medico())

    row = con.execute("SELECT * FROM medicos WHERE id = ?", (medico_id,)).fetchone()
    assert row["documento"] == "87654321"
    assert row["documento_enc"] is None

    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "migration-test-key")

    stats = _migrate(con, wipe_legacy=False)
    assert stats.backfilled == 1

    row = con.execute("SELECT * FROM medicos WHERE id = ?", (medico_id,)).fetchone()
    assert row["documento"] != "87654321"
    assert row["documento"] == row["documento_hash"]
    assert row["documento_enc"] is not None
    assert row["documento_hash"] is not None
    assert row["telefono"] == "611222333"
    assert row["email"] == "mario@clinic.test"
    assert row["direccion"] == "Avenida Sur 9"

    stats = _migrate(con, wipe_legacy=True)
    assert stats.backfilled == 0
    assert stats.wiped == 1

    row = con.execute("SELECT * FROM medicos WHERE id = ?", (medico_id,)).fetchone()
    assert row["documento"] == row["documento_hash"]
    assert row["telefono"] is None
    assert row["email"] is None
    assert row["direccion"] is None
    con.close()


def test_wipe_option_requires_data_path_and_confirmation(tmp_path: Path) -> None:
    options = MigrationOptions(
        db_path=tmp_path / "outside-data.sqlite",
        schema_path=_schema_path(),
        wipe_legacy=True,
        confirm_wipe="WIPE-LEGACY",
    )
    with pytest.raises(ValueError, match="solo permitido"):
        _validate_options(options)
