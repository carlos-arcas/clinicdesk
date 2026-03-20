from __future__ import annotations

from pathlib import Path

from scripts.quality_gate_components.doctor_entorno_calidad_core import (
    DiagnosticoEntornoCalidad,
    EstadoHerramienta,
    renderizar_reporte,
)
from scripts.quality_gate_components.toolchain import (
    COMANDO_REINSTALAR_LOCK,
    cargar_toolchain_esperado,
    leer_versiones_lock_desde_texto,
)


def test_leer_versiones_lock_omite_comentarios_y_includes() -> None:
    versiones = leer_versiones_lock_desde_texto(
        "\n".join(
            [
                "# lock dev",
                "-r requirements.txt",
                "ruff==0.8.4",
                "pytest==8.3.2",
                "",
            ]
        )
    )

    assert versiones == {"ruff": "0.8.4", "pytest": "8.3.2"}


def test_cargar_toolchain_esperado_lee_versiones_desde_lock(tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.in").write_text("ruff\npytest\nmypy\npip-audit\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text(
        "\n".join(
            [
                "ruff==0.8.4",
                "pytest==8.3.2",
                "mypy==1.13.0",
                "pip-audit==2.7.3",
            ]
        ),
        encoding="utf-8",
    )

    toolchain = cargar_toolchain_esperado(tmp_path)

    assert toolchain.version_esperada("ruff") == "0.8.4"
    assert toolchain.version_esperada("pip-audit") == "2.7.3"


def test_renderizar_reporte_muestra_error_accionable_para_tool_faltante(tmp_path: Path) -> None:
    diagnostico = DiagnosticoEntornoCalidad(
        python_activo="3.12.1",
        venv_activo=True,
        cache_pip="/tmp/pip-cache",
        wheelhouse=tmp_path / "wheelhouse",
        wheelhouse_disponible=False,
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
