from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("cryptography", reason="Falta dependencia opcional cryptography en este entorno")

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.db import bootstrap
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from scripts import security_cli


def _schema_path() -> Path:
    return Path("clinicdesk/app/infrastructure/sqlite/schema.sql").resolve()


def _build_paciente() -> Paciente:
    return Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="11112222",
        nombre="Nora",
        apellidos="Segura",
        telefono="612000111",
        email="nora@clinic.test",
        fecha_nacimiento=date(1990, 1, 1),
        direccion="Calle Audit 7",
        activo=True,
        num_historia=None,
        alergias=None,
        observaciones=None,
    )


def test_rotate_dry_run_no_imprime_pii_ni_claves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "crypto-rotate-dry.sqlite"
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "O" * 32 + "old-material")
    con = bootstrap(db_path, _schema_path(), apply=True)
    repo = PacientesRepository(con)
    repo.create(_build_paciente())
    con.close()

    clave_nueva = "N" * 32 + "new-material"
    clave_vieja = "O" * 32 + "old-material"
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", clave_nueva)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY_PREVIOUS", clave_vieja)

    exit_code = security_cli.main([
        "rotate-key",
        "--dry-run",
        "--db-path",
        db_path.as_posix(),
        "--schema-path",
        _schema_path().as_posix(),
    ])

    captured = capsys.readouterr()
    salida = f"{captured.out}\n{captured.err}"
    assert exit_code == 0
    assert "DRY-RUN OK" in captured.out
    assert "11112222" not in salida
    assert "nora@clinic.test" not in salida
    assert clave_nueva not in salida
    assert clave_vieja not in salida


def test_rotate_apply_recifra_y_permite_lectura(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "crypto-rotate-apply.sqlite"
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "O" * 32 + "old-material")

    con = bootstrap(db_path, _schema_path(), apply=True)
    repo = PacientesRepository(con)
    paciente_id = repo.create(_build_paciente())
    before = con.execute("SELECT documento_enc FROM pacientes WHERE id = ?", (paciente_id,)).fetchone()["documento_enc"]
    con.close()

    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "N" * 32 + "new-material")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY_PREVIOUS", "O" * 32 + "old-material")

    exit_code = security_cli.main([
        "rotate-key",
        "--apply",
        "--db-path",
        db_path.as_posix(),
        "--schema-path",
        _schema_path().as_posix(),
        "--batch-size",
        "10",
    ])
    assert exit_code == 0

    con_check = bootstrap(db_path, _schema_path(), apply=True)
    after = con_check.execute("SELECT documento_enc FROM pacientes WHERE id = ?", (paciente_id,)).fetchone()["documento_enc"]
    assert after is not None
    assert after != before

    paciente = PacientesRepository(con_check).get_by_id(paciente_id)
    assert paciente is not None
    assert paciente.documento == "11112222"

    audit_row = con_check.execute(
        "SELECT action, outcome, metadata_json FROM auditoria_eventos WHERE action = 'CRYPTO_ROTATE' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert audit_row is not None
    assert audit_row["outcome"] == "ok"
    assert "11112222" not in (audit_row["metadata_json"] or "")
    con_check.close()
