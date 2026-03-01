from __future__ import annotations

from pathlib import Path

import pytest

from clinicdesk.app.bootstrap import bootstrap_database


def test_bootstrap_requires_crypto_key_when_field_crypto_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    monkeypatch.delenv("CLINICDESK_CRYPTO_KEY", raising=False)

    with pytest.raises(RuntimeError, match="CLINICDESK_CRYPTO_KEY"):
        bootstrap_database(apply_schema=False, sqlite_path=(tmp_path / "missing-key.sqlite").as_posix())


def test_bootstrap_allows_start_without_key_when_field_crypto_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "0")
    monkeypatch.delenv("CLINICDESK_CRYPTO_KEY", raising=False)

    con = bootstrap_database(apply_schema=False, sqlite_path=(tmp_path / "no-key.sqlite").as_posix())
    con.close()
