from __future__ import annotations

from pathlib import Path

from scripts.quality_gate_components.doctor_entorno_calidad_core import (
    DiagnosticoEntornoCalidad,
    EstadoHerramienta,
    renderizar_reporte,
)
from scripts.quality_gate_components.entorno_python import EstadoInterprete
from scripts.quality_gate_components.toolchain import (
    COMANDO_REINSTALAR_LOCK,
    cargar_interprete_esperado,
    cargar_toolchain_esperado,
    leer_paquetes_input_desde_texto,
    leer_versiones_lock_desde_texto,
)


INTERPRETE_OK = EstadoInterprete(
    version_minima_repo="3.11",
    python_esperado="/tmp/repo/.venv/bin/python",
    python_activo="3.12.1",
    python_path="/tmp/repo/.venv/bin/python",
    venv_activo=True,
    venv_path="/tmp/repo/.venv",
    usa_python_repo=True,
    version_compatible=True,
    detalle="El intérprete activo coincide con .venv del repo.",
    comando_activar="source /tmp/repo/.venv/bin/activate",
    comando_recrear="rm -rf /tmp/repo/.venv && python scripts/setup.py",
)


def test_leer_versiones_lock_omite_comentarios_y_includes() -> None:
    versiones = leer_versiones_lock_desde_texto(
        "\n".join(["# lock dev", "-r requirements.txt", "ruff==0.8.4", "pytest==8.3.2", ""])
    )
    assert versiones == {"ruff": "0.8.4", "pytest": "8.3.2"}


def test_cargar_toolchain_esperado_lee_versiones_desde_lock(tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.in").write_text("ruff\npytest\nmypy\npip-audit\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text(
        "ruff==0.8.4\npytest==8.3.2\nmypy==1.13.0\npip-audit==2.7.3\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text('[tool.mypy]\npython_version = "3.11"\n', encoding="utf-8")

    toolchain = cargar_toolchain_esperado(tmp_path)
    interprete = cargar_interprete_esperado(tmp_path)

    assert toolchain.version_esperada("ruff") == "0.8.4"
    assert toolchain.version_esperada("pip-audit") == "2.7.3"
    assert interprete.version_minima == "3.11"
    assert interprete.python_repo == tmp_path / ".venv" / "bin" / "python"


def test_renderizar_reporte_muestra_error_accionable_para_tool_faltante(tmp_path: Path) -> None:
    diagnostico = DiagnosticoEntornoCalidad(
        interprete=INTERPRETE_OK,
        cache_pip="/tmp/pip-cache",
        wheelhouse=tmp_path / "wheelhouse",
        wheelhouse_estado="ausente",
        wheelhouse_disponible=False,
        wheelhouse_detalle="directorio ausente",
        wheelhouse_faltantes=(),
        indice_pip=None,
        proxy_configurado=False,
        diagnostico_red="sin wheelhouse ni proxy/index explícito; una red restringida bloqueará la reinstalación.",
        herramientas=(
            EstadoHerramienta(
                nombre="ruff",
                version_esperada="0.8.4",
                instalada=False,
                version_instalada=None,
                detalle_error="No module named ruff",
                bloquea_gate=True,
                comando_corregir=COMANDO_REINSTALAR_LOCK,
            ),
        ),
        toolchain_error=None,
        source_of_truth="requirements-dev.txt (versiones fijadas) + requirements-dev.in (entrada editable)",
    )

    lineas = renderizar_reporte(diagnostico)
    assert any("ruff: falta en el entorno; gate bloqueado" in linea for linea in lineas)
    assert any(COMANDO_REINSTALAR_LOCK in linea for linea in lineas)
    assert any("gate real seguirá fallando por entorno" in linea for linea in lineas)


def test_renderizar_reporte_explica_interprete_fuera_del_repo(tmp_path: Path) -> None:
    diagnostico = DiagnosticoEntornoCalidad(
        interprete=EstadoInterprete(
            version_minima_repo="3.11",
            python_esperado="/tmp/repo/.venv/bin/python",
            python_activo="3.12.1",
            python_path="/usr/bin/python3",
            venv_activo=False,
            venv_path=None,
            usa_python_repo=False,
            version_compatible=True,
            detalle="Estás fuera del venv del repo; el tooling visible puede pertenecer a otro entorno o al sistema.",
            comando_activar="source /tmp/repo/.venv/bin/activate",
            comando_recrear="rm -rf /tmp/repo/.venv && python scripts/setup.py",
        ),
        cache_pip=None,
        wheelhouse=tmp_path / "wheelhouse",
        wheelhouse_estado="ausente",
        wheelhouse_disponible=False,
        wheelhouse_detalle="directorio ausente",
        wheelhouse_faltantes=(),
        indice_pip=None,
        proxy_configurado=False,
        diagnostico_red="sin wheelhouse ni proxy/index explícito; una red restringida bloqueará la reinstalación.",
        herramientas=(),
        toolchain_error=None,
        source_of_truth="requirements-dev.txt (versiones fijadas) + requirements-dev.in (entrada editable)",
    )

    lineas = renderizar_reporte(diagnostico)
    assert any("Python esperado .venv" in linea for linea in lineas)
    assert any("Activa el venv correcto" in linea for linea in lineas)
    assert any("recréalo con" in linea for linea in lineas)


def test_leer_paquetes_input_omite_includes_y_conserva_paquetes() -> None:
    paquetes = leer_paquetes_input_desde_texto("# lock dev\n-r requirements.in\nruff\npytest==8.3.2\n")
    assert paquetes == ("ruff", "pytest")


def test_cargar_toolchain_esperado_falla_si_input_y_lock_no_coinciden(tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.in").write_text("ruff\npytest\nmypy\npip-audit\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.8.4\npytest==8.3.2\nmypy==1.13.0\n", encoding="utf-8")

    try:
        cargar_toolchain_esperado(tmp_path)
    except RuntimeError as exc:
        assert "pip-audit" in str(exc)
        assert "Regénéralo con python -m scripts.lock_deps" in str(exc)
    else:
        raise AssertionError("Se esperaba error si requirements-dev.in y requirements-dev.txt no coinciden")
