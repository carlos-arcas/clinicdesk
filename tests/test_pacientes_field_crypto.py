from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("cryptography", reason="Falta dependencia opcional cryptography en este entorno")

from clinicdesk.app.common.crypto_field_protection import decrypt, encrypt, hash_lookup
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository


def _schema_path() -> Path:
    return Path("clinicdesk/app/infrastructure/sqlite/schema.sql").resolve()


def _build_paciente() -> Paciente:
    return Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="12345678",
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


def test_crypto_field_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "test-key-material")
    token = encrypt("valor-secreto")
    assert token != "valor-secreto"
    assert decrypt(token) == "valor-secreto"


def test_hash_lookup_is_stable_after_normalization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "test-key-material")
    left = hash_lookup("  Ana   Paredes@example.test ")
    right = hash_lookup("ana paredes@example.test")
    assert left == right


def test_sqlite_pacientes_stores_ciphertext_when_feature_flag_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.delenv("CLINICDESK_PII_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "test-key-material")

    db_path = tmp_path / "field-crypto.sqlite"
    con = db.bootstrap(db_path, _schema_path(), apply=True)
    repo = PacientesRepository(con)
    paciente_id = repo.create(_build_paciente())

    row = con.execute(
        """
        SELECT documento, documento_enc, documento_hash,
               telefono, telefono_enc, telefono_hash,
               email, email_enc, email_hash,
               direccion, direccion_enc, direccion_hash
        FROM pacientes WHERE id = ?
        """,
        (paciente_id,),
    ).fetchone()

    assert row["documento"] == row["documento_hash"]
    assert row["telefono"] is None
    assert row["email"] is None
    assert row["direccion"] is None
    assert row["documento_enc"] is not None
    assert row["documento_hash"] is not None

    loaded = repo.get_by_id(paciente_id)
    assert loaded is not None
    assert loaded.documento == "12345678"
    assert loaded.telefono == "600999888"
    assert loaded.email == "ana@clinic.test"
    assert loaded.direccion == "Calle Secreta 123"

    con.execute("PRAGMA wal_checkpoint(FULL);")
    con.close()
    all_bytes = b""
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{db_path}{suffix}")
        if candidate.exists():
            all_bytes += candidate.read_bytes()

    for secret in (b"12345678", b"600999888", b"ana@clinic.test", b"Calle Secreta 123"):
        assert secret not in all_bytes
