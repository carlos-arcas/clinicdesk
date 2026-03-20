from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HerramientaToolchain:
    nombre_paquete: str
    modulo_python: str
    comando_version: tuple[str, ...] = ("--version",)
    usar_metadata: bool = False


HERRAMIENTAS_GATE: tuple[HerramientaToolchain, ...] = (
    HerramientaToolchain("ruff", "ruff"),
    HerramientaToolchain("pytest", "pytest"),
    HerramientaToolchain("mypy", "mypy"),
    HerramientaToolchain("pip-audit", "pip_audit", usar_metadata=True),
)

COMANDO_REINSTALAR_LOCK = "python -m pip install -r requirements-dev.txt"
COMANDO_REGENERAR_LOCK = "python -m scripts.lock_deps"
COMANDO_DOCTOR = "python -m scripts.doctor_entorno_calidad"
COMANDO_SETUP = "python scripts/setup.py"
COMANDO_GATE = "python -m scripts.gate_pr"
COMANDO_BUILD_WHEELHOUSE = "python -m scripts.dev.build_wheelhouse"


@dataclass(frozen=True)
class ToolchainEsperado:
    herramientas: tuple[HerramientaToolchain, ...]
    versiones: dict[str, str]
    requirements_dev_lock: Path
    requirements_dev_input: Path

    def version_esperada(self, nombre_paquete: str) -> str | None:
        return self.versiones.get(nombre_paquete)


class ErrorToolchain(RuntimeError):
    """Error de configuración del toolchain esperado."""


def cargar_toolchain_esperado(repo_root: Path) -> ToolchainEsperado:
    requirements_dev_lock = repo_root / "requirements-dev.txt"
    requirements_dev_input = repo_root / "requirements-dev.in"
    versiones = _leer_versiones_lock(requirements_dev_lock)
    return ToolchainEsperado(
        herramientas=HERRAMIENTAS_GATE,
        versiones=versiones,
        requirements_dev_lock=requirements_dev_lock,
        requirements_dev_input=requirements_dev_input,
    )


def leer_versiones_lock_desde_texto(texto_lock: str) -> dict[str, str]:
    versiones: dict[str, str] = {}
    for linea in texto_lock.splitlines():
        contenido = _normalizar_linea(linea)
        if contenido is None:
            continue
        nombre, separador, version = contenido.partition("==")
        if separador != "==":
            continue
        versiones[nombre] = version
    return versiones


def _leer_versiones_lock(requirements_dev_lock: Path) -> dict[str, str]:
    if not requirements_dev_lock.exists():
        raise ErrorToolchain(
            f"Falta el lock dev obligatorio: {requirements_dev_lock}. Regénéralo con {COMANDO_REGENERAR_LOCK}."
        )

    versiones = leer_versiones_lock_desde_texto(requirements_dev_lock.read_text(encoding="utf-8"))

    faltantes = [herramienta.nombre_paquete for herramienta in HERRAMIENTAS_GATE if herramienta.nombre_paquete not in versiones]
    if faltantes:
        faltantes_render = ", ".join(faltantes)
        raise ErrorToolchain(
            "El lock dev no define todas las herramientas del gate "
            f"({faltantes_render}) en {requirements_dev_lock}. Regénéralo con {COMANDO_REGENERAR_LOCK}."
        )
    return versiones


def _normalizar_linea(linea: str) -> str | None:
    contenido = linea.strip()
    if not contenido or contenido.startswith("#"):
        return None
    if contenido.startswith(("-", "--")):
        return None
    return contenido.split(" ", maxsplit=1)[0].strip()
