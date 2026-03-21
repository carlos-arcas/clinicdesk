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
    paquetes_input = _leer_paquetes_input(requirements_dev_input)
    _validar_coherencia_input_y_lock(requirements_dev_lock, requirements_dev_input, versiones, paquetes_input)
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




def version_paquete_desde_lock(repo_root: Path, nombre_paquete: str) -> str | None:
    requirements_dev_lock = repo_root / "requirements-dev.txt"
    versiones = _leer_versiones_lock(requirements_dev_lock, validar_herramientas_gate=False)
    return versiones.get(nombre_paquete)

def leer_paquetes_input_desde_texto(texto_input: str) -> tuple[str, ...]:
    paquetes: list[str] = []
    for linea in texto_input.splitlines():
        contenido = _normalizar_linea(linea)
        if contenido is None:
            continue
        nombre = contenido.split("==", maxsplit=1)[0].strip()
        if nombre:
            paquetes.append(nombre)
    return tuple(paquetes)


def _leer_versiones_lock(requirements_dev_lock: Path, *, validar_herramientas_gate: bool = True) -> dict[str, str]:
    if not requirements_dev_lock.exists():
        raise ErrorToolchain(
            f"Falta el lock dev obligatorio: {requirements_dev_lock}. Regénéralo con {COMANDO_REGENERAR_LOCK}."
        )

    versiones = leer_versiones_lock_desde_texto(requirements_dev_lock.read_text(encoding="utf-8"))
    faltantes = [herramienta.nombre_paquete for herramienta in HERRAMIENTAS_GATE if herramienta.nombre_paquete not in versiones]
    if validar_herramientas_gate and faltantes:
        faltantes_render = ", ".join(faltantes)
        raise ErrorToolchain(
            "El lock dev no define todas las herramientas del gate "
            f"({faltantes_render}) en {requirements_dev_lock}. Regénéralo con {COMANDO_REGENERAR_LOCK}."
        )
    return versiones


def _leer_paquetes_input(requirements_dev_input: Path) -> tuple[str, ...]:
    if not requirements_dev_input.exists():
        raise ErrorToolchain(
            f"Falta la entrada editable dev: {requirements_dev_input}. Regénérala o recupérala antes de usar {COMANDO_REGENERAR_LOCK}."
        )
    return leer_paquetes_input_desde_texto(requirements_dev_input.read_text(encoding="utf-8"))


def _validar_coherencia_input_y_lock(
    requirements_dev_lock: Path,
    requirements_dev_input: Path,
    versiones: dict[str, str],
    paquetes_input: tuple[str, ...],
) -> None:
    faltantes_input = [paquete for paquete in paquetes_input if paquete not in versiones]
    if faltantes_input:
        faltantes_render = ", ".join(faltantes_input)
        raise ErrorToolchain(
            "La entrada editable y el lock dev están desalineados: "
            f"{requirements_dev_input.name} declara {faltantes_render} pero {requirements_dev_lock.name} no los fija. "
            f"Regénéralo con {COMANDO_REGENERAR_LOCK}."
        )


def _normalizar_linea(linea: str) -> str | None:
    contenido = linea.strip()
    if not contenido or contenido.startswith("#"):
        return None
    if contenido.startswith(("-", "--")):
        return None
    return contenido.split(" ", maxsplit=1)[0].strip()
