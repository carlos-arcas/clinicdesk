from __future__ import annotations

from pathlib import Path

from scripts.quality_gate_components import bootstrap_dependencias


def _escribir_locks(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("PySide6==6.8.3\ncryptography==46.0.5\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text(
        "coverage==7.6.10\n-r requirements.txt\npytest==8.3.2\nruff==0.8.4\n",
        encoding="utf-8",
    )


def test_comando_instalacion_offline_si_wheelhouse_cubre_lock(tmp_path: Path) -> None:
    _escribir_locks(tmp_path)
    requirements = tmp_path / "requirements-dev.txt"
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    for wheel in (
        "coverage-7.6.10-py3-none-any.whl",
        "cryptography-46.0.5-cp311-abi3-manylinux.whl",
        "PySide6-6.8.3-cp39-abi3-manylinux.whl",
        "pytest-8.3.2-py3-none-any.whl",
        "ruff-0.8.4-py3-none-any.whl",
    ):
        (wheelhouse / wheel).write_text("x", encoding="utf-8")

    comando, modo = bootstrap_dependencias.comando_instalacion("python", requirements, wheelhouse, tmp_path)

    assert modo == "offline"
    assert "--no-index" in comando
    assert "--find-links" in comando


def test_comando_instalacion_online_si_wheelhouse_no_cubre_lock(tmp_path: Path) -> None:
    _escribir_locks(tmp_path)
    requirements = tmp_path / "requirements-dev.txt"
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    (wheelhouse / "pytest-8.3.2-py3-none-any.whl").write_text("x", encoding="utf-8")

    comando, modo = bootstrap_dependencias.comando_instalacion("python", requirements, wheelhouse, tmp_path)

    assert modo == "online"
    assert "--no-index" not in comando


def test_diagnosticar_wheelhouse_distingue_vacio_incompleto_y_utilizable(tmp_path: Path) -> None:
    _escribir_locks(tmp_path)
    wheelhouse = tmp_path / "wheelhouse"

    ausente = bootstrap_dependencias.diagnosticar_wheelhouse_desde_lock(tmp_path, wheelhouse)
    assert ausente.codigo == "ausente"

    wheelhouse.mkdir()
    vacio = bootstrap_dependencias.diagnosticar_wheelhouse_desde_lock(tmp_path, wheelhouse)
    assert vacio.codigo == "vacio"

    (wheelhouse / "pytest-8.3.2-py3-none-any.whl").write_text("x", encoding="utf-8")
    incompleto = bootstrap_dependencias.diagnosticar_wheelhouse_desde_lock(tmp_path, wheelhouse)
    assert incompleto.codigo == "incompleto"
    assert "pyside6==6.8.3" in incompleto.paquetes_faltantes

    for wheel in (
        "coverage-7.6.10-py3-none-any.whl",
        "cryptography-46.0.5-cp311-abi3-manylinux.whl",
        "PySide6-6.8.3-cp39-abi3-manylinux.whl",
        "ruff-0.8.4-py3-none-any.whl",
    ):
        (wheelhouse / wheel).write_text("x", encoding="utf-8")
    utilizable = bootstrap_dependencias.diagnosticar_wheelhouse_desde_lock(tmp_path, wheelhouse)
    assert utilizable.codigo == "utilizable"
