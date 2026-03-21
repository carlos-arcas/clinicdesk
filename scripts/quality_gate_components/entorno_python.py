from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys

from .toolchain import InterpreteEsperado


@dataclass(frozen=True)
class EstadoInterprete:
    version_minima_repo: str
    python_esperado: str
    python_activo: str
    python_path: str
    venv_activo: bool
    venv_path: str | None
    usa_python_repo: bool
    version_compatible: bool
    detalle: str
    comando_activar: str
    comando_recrear: str


def diagnosticar_interprete(interprete_esperado: InterpreteEsperado) -> EstadoInterprete:
    python_activo = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_path = str(Path(sys.executable).resolve())
    venv_path = os.environ.get("VIRTUAL_ENV")
    usa_python_repo = Path(python_path) == interprete_esperado.python_repo.resolve()
    version_compatible = sys.version_info >= _parsear_version_minima(interprete_esperado.version_minima)
    return EstadoInterprete(
        version_minima_repo=interprete_esperado.version_minima,
        python_esperado=str(interprete_esperado.python_repo),
        python_activo=python_activo,
        python_path=python_path,
        venv_activo=venv_activo(),
        venv_path=venv_path,
        usa_python_repo=usa_python_repo,
        version_compatible=version_compatible,
        detalle=_detalle_interprete(interprete_esperado, python_path, venv_path, usa_python_repo, version_compatible),
        comando_activar=interprete_esperado.comando_activar,
        comando_recrear=interprete_esperado.comando_recrear,
    )


def venv_activo() -> bool:
    if os.environ.get("VIRTUAL_ENV"):
        return True
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def lineas_ayuda_interprete(interprete: EstadoInterprete) -> list[str]:
    if interprete.usa_python_repo:
        return []
    return [
        f"[doctor][warn] {interprete.detalle}",
        f"[doctor][accion] Activa el venv correcto: {interprete.comando_activar}",
        f"[doctor][accion] Si el venv quedó roto o usa otro Python, recréalo con: {interprete.comando_recrear}",
    ]


def _detalle_interprete(
    interprete_esperado: InterpreteEsperado,
    python_path: str,
    venv_path: str | None,
    usa_python_repo: bool,
    version_compatible: bool,
) -> str:
    if not version_compatible:
        return (
            f"Python activo incompatible con el repo: usa >= {interprete_esperado.version_minima}. "
            f"Recrea el entorno con {interprete_esperado.comando_recrear}."
        )
    if usa_python_repo:
        return "El intérprete activo coincide con .venv del repo."
    if not venv_activo():
        return (
            "Estás fuera del venv del repo; el tooling visible puede pertenecer a otro entorno o al sistema. "
            f"Activa {interprete_esperado.comando_activar} o recrea con {interprete_esperado.comando_recrear}."
        )
    if venv_path:
        return (
            f"Hay un venv activo distinto al esperado ({venv_path}); el tooling instalado puede venir de otro entorno. "
            f"Activa {interprete_esperado.comando_activar} o recrea con {interprete_esperado.comando_recrear}."
        )
    return (
        f"El intérprete activo ({python_path}) no coincide con {interprete_esperado.python_repo}; "
        f"activa {interprete_esperado.comando_activar} o recrea con {interprete_esperado.comando_recrear}."
    )


def _parsear_version_minima(version: str) -> tuple[int, ...]:
    return tuple(int(parte) for parte in version.split("."))
