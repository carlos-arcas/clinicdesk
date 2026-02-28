from __future__ import annotations

from pathlib import Path

from clinicdesk.app.bootstrap import resolve_db_path


def test_resolve_db_path_uses_arg_over_env(monkeypatch) -> None:
    monkeypatch.setenv("CLINICDESK_DB_PATH", "/tmp/from-env.db")

    resolved = resolve_db_path("./data/from-arg.db", emit_log=False)

    assert resolved == Path("./data/from-arg.db").resolve()


def test_resolve_db_path_uses_env_when_no_arg(monkeypatch) -> None:
    monkeypatch.setenv("CLINICDESK_DB_PATH", "/tmp/from-env.db")

    resolved = resolve_db_path(None, emit_log=False)

    assert resolved == Path("/tmp/from-env.db").resolve()


def test_resolve_db_path_uses_official_default(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CLINICDESK_DB_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    resolved = resolve_db_path(None, emit_log=False)

    assert resolved == (tmp_path / "data" / "clinicdesk.db").resolve()
