from __future__ import annotations

from scripts.quality_gate_components.sandbox_mode import sandbox_mode_activo


def test_sandbox_mode_activo_con_variable_en_1() -> None:
    assert sandbox_mode_activo({"CLINICDESK_SANDBOX_MODE": "1"}) is True


def test_sandbox_mode_inactivo_sin_variable() -> None:
    assert sandbox_mode_activo({}) is False
