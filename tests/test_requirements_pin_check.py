from __future__ import annotations

import ast
from pathlib import Path

from scripts.quality_gate_components import requirements_pin_check


def _usa_testclient_fastapi_o_starlette(ruta_test: Path) -> bool:
    arbol = ast.parse(ruta_test.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            if any(alias.name in {"fastapi.testclient", "starlette.testclient"} for alias in nodo.names):
                return True
            continue
        if not isinstance(nodo, ast.ImportFrom):
            continue
        modulo = nodo.module or ""
        if modulo in {"fastapi.testclient", "starlette.testclient"}:
            return True
    return False


def _contiene_dependencia(ruta_requirements: Path, dependencia: str) -> bool:
    objetivo = dependencia.lower()
    for linea in ruta_requirements.read_text(encoding="utf-8").splitlines():
        contenido = linea.strip()
        if not contenido or contenido.startswith(("#", "-")):
            continue
        if contenido.split("==", maxsplit=1)[0].lower() == objetivo:
            return True
    return False


def _contiene_dependencia_pinneada(ruta_requirements: Path, dependencia: str) -> bool:
    objetivo = f"{dependencia.lower()}=="
    for linea in ruta_requirements.read_text(encoding="utf-8").splitlines():
        contenido = linea.strip().lower()
        if contenido.startswith(objetivo):
            return True
    return False


def test_linea_esta_pinneada_acepta_formato_valido() -> None:
    assert requirements_pin_check.linea_esta_pinneada("pytest==8.3.2")
    assert requirements_pin_check.linea_esta_pinneada("  # comentario")
    assert requirements_pin_check.linea_esta_pinneada("-r requirements.txt")


def test_validar_requirements_pinneados_detecta_rangos(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "pytest==8.3.2\nruff>=0.8\ncryptography<47\n",
        encoding="utf-8",
    )

    errores = requirements_pin_check.validar_requirements_pinneados(requirements)

    assert errores == [(2, "ruff>=0.8"), (3, "cryptography<47")]


def test_check_requirements_pinneados_falla_si_hay_linea_no_pinneada(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("pytest==8.3.2\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff>=0.8\n", encoding="utf-8")

    assert requirements_pin_check.check_requirements_pinneados(repo_root=tmp_path) == 9


def test_httpx_obligatorio_si_hay_testclient_en_tests() -> None:
    raiz_repo = Path(__file__).resolve().parents[1]
    tests_con_testclient = [
        ruta for ruta in (raiz_repo / "tests").glob("test_*.py") if _usa_testclient_fastapi_o_starlette(ruta)
    ]
    if not tests_con_testclient:
        return

    requirements_in = raiz_repo / "requirements-dev.in"
    requirements_dev = raiz_repo / "requirements-dev.txt"
    assert _contiene_dependencia(requirements_in, "httpx"), (
        "Se detectaron tests que importan fastapi/starlette testclient y falta 'httpx' en requirements-dev.in: "
        + ", ".join(ruta.name for ruta in tests_con_testclient)
    )
    assert _contiene_dependencia_pinneada(requirements_dev, "httpx"), (
        "Se detectaron tests que importan fastapi/starlette testclient y falta 'httpx' pinneado en requirements-dev.txt: "
        + ", ".join(ruta.name for ruta in tests_con_testclient)
    )
