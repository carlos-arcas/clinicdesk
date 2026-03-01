from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("cryptography", reason="Falta dependencia opcional cryptography en este entorno")

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository
from clinicdesk.app.queries.personal_queries import PersonalQueries


def _schema_path() -> Path:
    return Path("clinicdesk/app/infrastructure/sqlite/schema.sql").resolve()


def _build_personal() -> Personal:
    return Personal(
        tipo_documento=TipoDocumento.DNI,
        documento="55667788",
        nombre="Elena",
        apellidos="Ruiz",
        telefono="612345678",
        email="elena@clinic.test",
        fecha_nacimiento=date(1991, 9, 11),
        direccion="Calle Luna 7",
        activo=True,
        puesto="Recepcion",
        turno=None,
    )


def test_sqlite_personal_stores_ciphertext_when_feature_flag_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.delenv("CLINICDESK_PII_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "test-key-material")

    db_path = tmp_path / "field-crypto-personal.sqlite"
    con = db.bootstrap(db_path, _schema_path(), apply=True)
    repo = PersonalRepository(con)
    personal_id = repo.create(_build_personal())

    row = con.execute(
        """
        SELECT documento, documento_enc, documento_hash,
               telefono, telefono_enc, telefono_hash,
               email, email_enc, email_hash,
               direccion, direccion_enc, direccion_hash
        FROM personal WHERE id = ?
        """,
        (personal_id,),
    ).fetchone()

    assert row["documento"] == row["documento_hash"]
    assert row["telefono"] is None
    assert row["email"] is None
    assert row["direccion"] is None
    assert row["documento_enc"] is not None
    assert row["documento_hash"] is not None

    loaded = repo.get_by_id(personal_id)
    assert loaded is not None
    assert loaded.documento == "55667788"
    assert loaded.telefono == "612345678"
    assert loaded.email == "elena@clinic.test"
    assert loaded.direccion == "Calle Luna 7"
    assert repo.get_id_by_documento(TipoDocumento.DNI, "55667788") == personal_id

    query_rows = PersonalQueries(con).search(documento="55667788")
    assert [item.id for item in query_rows] == [personal_id]

    con.execute("PRAGMA wal_checkpoint(FULL);")
    con.close()
    all_bytes = b""
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{db_path}{suffix}")
        if candidate.exists():
            all_bytes += candidate.read_bytes()

    for secret in (b"55667788", b"612345678", b"elena@clinic.test", b"Calle Luna 7"):
        assert secret not in all_bytes
