from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("cryptography", reason="Falta dependencia opcional cryptography en este entorno")

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.db import bootstrap
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from scripts import security_cli

_CLAVE_VIEJA = "O" * 32 + "old-material"
_CLAVE_NUEVA = "N" * 32 + "new-material"
_PII_ESPERADA = ("11112222", "nora@clinic.test", "612000111", "Calle Audit 7", _CLAVE_VIEJA, _CLAVE_NUEVA)


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


def _configurar_entorno(monkeypatch: pytest.MonkeyPatch, *, clave_activa: str = _CLAVE_VIEJA) -> None:
    monkeypatch.setenv("CLINICDESK_PII_ENCRYPTION_ENABLED", "0")
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", clave_activa)


def _seed_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, int, str]:
    _configurar_entorno(monkeypatch)
    db_path = tmp_path / "crypto-security.sqlite"
    con = bootstrap(db_path, _schema_path(), apply=True)
    repo = PacientesRepository(con)
    paciente_id = repo.create(_build_paciente())
    documento_enc = con.execute("SELECT documento_enc FROM pacientes WHERE id = ?", (paciente_id,)).fetchone()["documento_enc"]
    con.close()
    return db_path, paciente_id, documento_enc


def _assert_sin_fuga(texto: str) -> None:
    for secreto in _PII_ESPERADA:
        assert secreto not in texto


def test_generate_key_emite_formato_razonable_y_advertencia_segura(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", _CLAVE_VIEJA)
    rc = security_cli.main(["generate-key"])

    captured = capsys.readouterr()
    clave = captured.out.strip()
    assert rc == 0
    assert clave
    assert len(clave) >= 48
    assert re.fullmatch(r"[A-Za-z0-9_-]+", clave)
    assert "ADVERTENCIA" in captured.err
    _assert_sin_fuga(f"{captured.out}\n{captured.err}")


def test_check_key_reporta_ok_y_fallo_claro(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", _CLAVE_NUEVA)
    ok_rc = security_cli.main(["check-key"])
    ok = capsys.readouterr()

    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "debil")
    fail_rc = security_cli.main(["check-key"])
    fail = capsys.readouterr()

    monkeypatch.delenv("CLINICDESK_CRYPTO_KEY", raising=False)
    missing_rc = security_cli.main(["check-key"])
    missing = capsys.readouterr()

    assert ok_rc == 0
    assert "OK: CLINICDESK_CRYPTO_KEY válida." in ok.out
    assert ok.err == ""
    assert fail_rc == 1
    assert "fortaleza insuficiente" in fail.err
    assert missing_rc == 1
    assert "ausente o con fortaleza insuficiente" in missing.err
    _assert_sin_fuga(f"{ok.out}\n{ok.err}\n{fail.out}\n{fail.err}\n{missing.out}\n{missing.err}")


def test_rotate_dry_run_reporta_contadores_y_no_filtra_pii(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path, _, _ = _seed_db(tmp_path, monkeypatch)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", _CLAVE_NUEVA)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY_PREVIOUS", _CLAVE_VIEJA)

    rc = security_cli.main(
        ["rotate-key", "--dry-run", "--db-path", db_path.as_posix(), "--schema-path", _schema_path().as_posix()]
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "DRY-RUN OK" in captured.out
    assert "filas_leidas=1" in captured.out
    assert "filas_actualizadas=0" in captured.out
    assert "campos_recifrados=4" in captured.out
    assert captured.err == ""
    _assert_sin_fuga(f"{captured.out}\n{captured.err}")


def test_rotate_apply_recifra_mantiene_lectura_y_audita_sin_pii(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path, paciente_id, documento_antes = _seed_db(tmp_path, monkeypatch)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", _CLAVE_NUEVA)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY_PREVIOUS", _CLAVE_VIEJA)

    rc = security_cli.main(
        [
            "rotate-key",
            "--apply",
            "--db-path",
            db_path.as_posix(),
            "--schema-path",
            _schema_path().as_posix(),
            "--batch-size",
            "10",
        ]
    )

    captured = capsys.readouterr()
    con = bootstrap(db_path, _schema_path(), apply=True)
    repo = PacientesRepository(con)
    row = con.execute(
        """
        SELECT documento_enc, telefono_enc, email_enc, direccion_enc
        FROM pacientes WHERE id = ?
        """,
        (paciente_id,),
    ).fetchone()
    audit_row = con.execute(
        """
        SELECT action, outcome, actor_username, actor_role, correlation_id, metadata_json
        FROM auditoria_eventos
        WHERE action = 'CRYPTO_ROTATE'
        ORDER BY id DESC LIMIT 1
        """
    ).fetchone()
    paciente = repo.get_by_id(paciente_id)
    con.close()

    assert rc == 0
    assert "APPLY OK" in captured.out
    assert "filas_leidas=1" in captured.out
    assert "filas_actualizadas=1" in captured.out
    assert "campos_recifrados=4" in captured.out
    _assert_sin_fuga(f"{captured.out}\n{captured.err}")
    assert row["documento_enc"] != documento_antes
    assert all(row[campo] and row[campo].startswith("cfp:v1:") for campo in row.keys())
    assert paciente is not None
    assert paciente.documento == "11112222"
    assert paciente.telefono == "612000111"
    assert paciente.email == "nora@clinic.test"
    assert paciente.direccion == "Calle Audit 7"
    assert audit_row is not None
    assert audit_row["outcome"] == "ok"
    assert audit_row["actor_username"] == "security_cli"
    assert audit_row["actor_role"] == "SYSTEM"
    assert audit_row["correlation_id"] is None

    metadata = json.loads(audit_row["metadata_json"])
    assert metadata == {
        "n_patients": 1,
        "warnings_count": 0,
        "movimientos": 4,
        "reason_code": "rotate_apply",
    }
    _assert_sin_fuga(audit_row["metadata_json"])


def test_rotate_key_sin_modo_falla_con_error_explicito() -> None:
    with pytest.raises(SystemExit) as exc:
        security_cli.main(["rotate-key"])

    assert exc.value.code == 2


def test_rotate_key_falla_con_entorno_invalido_y_previous_debil(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path, _, _ = _seed_db(tmp_path, monkeypatch)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", "debil")

    rc_activa = security_cli.main(
        ["rotate-key", "--dry-run", "--db-path", db_path.as_posix(), "--schema-path", _schema_path().as_posix()]
    )
    salida_activa = capsys.readouterr()

    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY", _CLAVE_NUEVA)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY_PREVIOUS", "weak")
    rc_previa = security_cli.main(
        ["rotate-key", "--dry-run", "--db-path", db_path.as_posix(), "--schema-path", _schema_path().as_posix()]
    )
    salida_previa = capsys.readouterr()

    assert rc_activa == 1
    assert "CLINICDESK_CRYPTO_KEY inválida." in salida_activa.err
    assert rc_previa == 1
    assert "CLINICDESK_CRYPTO_KEY_PREVIOUS inválida." in salida_previa.err
    _assert_sin_fuga(
        f"{salida_activa.out}\n{salida_activa.err}\n{salida_previa.out}\n{salida_previa.err}"
    )


def test_rotate_key_falla_si_faltan_columnas_de_cifrado(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configurar_entorno(monkeypatch, clave_activa=_CLAVE_NUEVA)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY_PREVIOUS", _CLAVE_VIEJA)
    db_path = tmp_path / "sin-columnas.sqlite"
    con = bootstrap(db_path, _schema_path(), apply=True)
    con.execute("DROP TABLE pacientes")
    con.execute("CREATE TABLE pacientes (id INTEGER PRIMARY KEY AUTOINCREMENT, documento TEXT)")
    con.commit()
    con.close()

    bootstrap_real = security_cli.bootstrap

    def _bootstrap_sin_apply(db_path_arg: Path, schema_path_arg: Path, *, apply: bool = True):
        return bootstrap_real(db_path_arg, schema_path_arg, apply=False)

    monkeypatch.setattr(security_cli, "bootstrap", _bootstrap_sin_apply)

    rc = security_cli.main(
        ["rotate-key", "--dry-run", "--db-path", db_path.as_posix(), "--schema-path", _schema_path().as_posix()]
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert "Faltan columnas de cifrado en pacientes." in captured.err


def test_rotate_key_falla_con_schema_inexistente_y_db_invalida(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configurar_entorno(monkeypatch, clave_activa=_CLAVE_NUEVA)
    monkeypatch.setenv("CLINICDESK_CRYPTO_KEY_PREVIOUS", _CLAVE_VIEJA)
    db_path = tmp_path / "db.sqlite"

    rc_schema = security_cli.main(
        [
            "rotate-key",
            "--dry-run",
            "--db-path",
            db_path.as_posix(),
            "--schema-path",
            (tmp_path / "missing.sql").as_posix(),
        ]
    )
    salida_schema = capsys.readouterr()

    db_path.write_text("esto no es sqlite", encoding="utf-8")
    rc_db = security_cli.main(
        ["rotate-key", "--dry-run", "--db-path", db_path.as_posix(), "--schema-path", _schema_path().as_posix()]
    )
    salida_db = capsys.readouterr()

    assert rc_schema == 1
    assert "No existe schema.sql" in salida_schema.err
    assert rc_db == 1
    assert "SQLite inválida o inaccesible" in salida_db.err
