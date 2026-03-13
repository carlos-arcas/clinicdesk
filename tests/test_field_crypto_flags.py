from __future__ import annotations

import pytest

from clinicdesk.app.common.field_crypto_flags import field_protection_enabled


@pytest.mark.parametrize("legacy_value", ["1", "true", "yes", "on"])
def test_flag_legacy_habilita_si_no_hay_flag_nueva(monkeypatch: pytest.MonkeyPatch, legacy_value: str) -> None:
    monkeypatch.delenv("SECURITY_FIELD_PROTECTION_ENABLED", raising=False)
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", legacy_value)
    assert field_protection_enabled() is True


def test_flag_nueva_tiene_precedencia_sobre_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECURITY_FIELD_PROTECTION_ENABLED", "0")
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "1")
    assert field_protection_enabled() is False

    monkeypatch.setenv("SECURITY_FIELD_PROTECTION_ENABLED", "1")
    monkeypatch.setenv("CLINICDESK_FIELD_CRYPTO", "0")
    assert field_protection_enabled() is True
