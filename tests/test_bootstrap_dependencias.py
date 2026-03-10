from __future__ import annotations

from pathlib import Path

from scripts.quality_gate_components import bootstrap_dependencias


def test_comando_instalacion_offline_si_hay_wheels(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements-dev.txt"
    requirements.write_text("pytest==8.3.2\n", encoding="utf-8")
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    (wheelhouse / "pytest-8.3.2-py3-none-any.whl").write_text("x", encoding="utf-8")

    comando, modo = bootstrap_dependencias.comando_instalacion("python", requirements, wheelhouse)

    assert modo == "offline"
    assert "--no-index" in comando
    assert "--find-links" in comando


def test_comando_instalacion_online_si_no_hay_wheels(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements-dev.txt"
    requirements.write_text("pytest==8.3.2\n", encoding="utf-8")

    comando, modo = bootstrap_dependencias.comando_instalacion("python", requirements, tmp_path / "wheelhouse")

    assert modo == "online"
    assert "--no-index" not in comando
