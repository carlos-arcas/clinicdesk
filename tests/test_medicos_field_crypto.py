from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("cryptography", reason="Falta dependencia opcional cryptography en este entorno")

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Medico
from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository


def _schema_path() -> Path:
    return Path("clinicdesk/app/infrastructure/sqlite/schema.sql").resolve()


def _build_medico() -> Medico:
    return Medico(
        tipo_documento=TipoDocumento.DNI,
        documento="11112222",
        nombre="Nora",
        apellidos="Luna",
        telefono="699333222",
        email="nora@clinic.test",
        fecha_nacimiento=date(1988, 5, 10),
        direccion="Calle Norte 45",
        activo=True,
        num_colegiado="COL-123",
        especialidad="Dermatología",
    )


def test_sqlite_medicos_stores_ciphertext_when_feature_flag_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.delenv("CLINICDESK_PII_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "test-key-material")

    db_path = tmp_path / "field-crypto-medicos.sqlite"
    con = db.bootstrap(db_path, _schema_path(), apply=True)
    repo = MedicosRepository(con)
    medico_id = repo.create(_build_medico())

    row = con.execute(
        """
        SELECT documento, documento_enc, documento_hash,
               telefono, telefono_enc, telefono_hash,
               email, email_enc, email_hash,
               direccion, direccion_enc, direccion_hash
        FROM medicos WHERE id = ?
        """,
        (medico_id,),
    ).fetchone()

    assert row["documento"] == row["documento_hash"]
    assert row["telefono"] is None
    assert row["email"] is None
    assert row["direccion"] is None
    assert row["documento_enc"] is not None
    assert row["documento_hash"] is not None

    loaded = repo.get_by_id(medico_id)
    assert loaded is not None
    assert loaded.documento == "11112222"
    assert loaded.telefono == "699333222"
    assert loaded.email == "nora@clinic.test"
    assert loaded.direccion == "Calle Norte 45"

    con.execute("PRAGMA wal_checkpoint(FULL);")
    con.close()
    all_bytes = b""
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{db_path}{suffix}")
        if candidate.exists():
            all_bytes += candidate.read_bytes()

    for secret in (b"11112222", b"699333222", b"nora@clinic.test", b"Calle Norte 45"):
        assert secret not in all_bytes
