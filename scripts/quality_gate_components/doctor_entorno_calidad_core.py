from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
import sys

HERRAMIENTAS_CRITICAS = {
    "ruff": "ruff",
    "pytest": "pytest",
    "mypy": "mypy",
    "pip-audit": "pip_audit",
}
PATRON_VERSION = re.compile(r"(?P<version>\d+\.\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class EstadoHerramienta:
    nombre: str
    version_esperada: str | None
    instalada: bool
    version_instalada: str | None
    detalle_error: str | None


@dataclass(frozen=True)
class DiagnosticoEntornoCalidad:
    python_activo: str
    venv_activo: bool
    cache_pip: str | None
    wheelhouse: Path
    wheelhouse_disponible: bool
    herramientas: tuple[EstadoHerramienta, ...]

    @property
    def tiene_faltantes(self) -> bool:
        return any(not herramienta.instalada for herramienta in self.herramientas)

    @property
    def tiene_desalineaciones(self) -> bool:
        for herramienta in self.herramientas:
            if not herramienta.instalada:
                continue
            if herramienta.version_esperada and herramienta.version_instalada != herramienta.version_esperada:
                return True
        return False


def diagnosticar_entorno_calidad(repo_root: Path, wheelhouse: Path | None = None) -> DiagnosticoEntornoCalidad:
    wheelhouse_path = _resolver_wheelhouse(repo_root, wheelhouse)
    return DiagnosticoEntornoCalidad(
        python_activo=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        venv_activo=_venv_activo(),
        cache_pip=_cache_pip(),
        wheelhouse=wheelhouse_path,
        wheelhouse_disponible=_wheelhouse_disponible(wheelhouse_path),
        herramientas=_estado_herramientas(repo_root),
    )


def codigo_salida_estable(diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool = False) -> int:
    if diagnostico.tiene_faltantes:
        return 2
    if diagnostico.tiene_desalineaciones:
        return 3
    if exigir_wheelhouse and not diagnostico.wheelhouse_disponible:
        return 4
    return 0


def renderizar_reporte(diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool = False) -> list[str]:
    lineas = [
        "[doctor] Diagnóstico de entorno de calidad",
        f"[doctor] Python activo: {diagnostico.python_activo}",
        f"[doctor] Venv activo: {'sí' if diagnostico.venv_activo else 'no'}",
        f"[doctor] pip cache dir: {diagnostico.cache_pip or 'no disponible'}",
        f"[doctor] Wheelhouse: {diagnostico.wheelhouse} ({'disponible' if diagnostico.wheelhouse_disponible else 'ausente'})",
    ]
    for herramienta in diagnostico.herramientas:
        lineas.extend(_lineas_herramienta(herramienta))
    lineas.extend(_lineas_ayuda(diagnostico, exigir_wheelhouse=exigir_wheelhouse))
    return lineas


def _resolver_wheelhouse(repo_root: Path, wheelhouse: Path | None) -> Path:
    if wheelhouse is not None:
        return wheelhouse
    valor_env = os.environ.get("CLINICDESK_WHEELHOUSE")
    if valor_env:
        return Path(valor_env).expanduser().resolve()
    return repo_root / "wheelhouse"


def _wheelhouse_disponible(wheelhouse: Path) -> bool:
    if not wheelhouse.exists() or not wheelhouse.is_dir():
        return False
    return any(wheelhouse.glob("*.whl"))


def _venv_activo() -> bool:
    if os.environ.get("VIRTUAL_ENV"):
        return True
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _cache_pip() -> str | None:
    comando = [sys.executable, "-m", "pip", "cache", "dir"]
    resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
    if resultado.returncode != 0:
        return None
    valor = (resultado.stdout or "").strip()
    return valor or None


def _versiones_pinneadas(repo_root: Path) -> dict[str, str]:
    versiones: dict[str, str] = {}
    requirements_dev = repo_root / "requirements-dev.txt"
    if not requirements_dev.exists():
        return versiones

    for linea in requirements_dev.read_text(encoding="utf-8").splitlines():
        contenido = linea.strip()
        if not contenido or contenido.startswith("#"):
            continue
        for nombre in HERRAMIENTAS_CRITICAS:
            if contenido.startswith(f"{nombre}=="):
                versiones[nombre] = contenido.split("==", maxsplit=1)[1].strip()
    return versiones


def _estado_herramientas(repo_root: Path) -> tuple[EstadoHerramienta, ...]:
    versiones = _versiones_pinneadas(repo_root)
    estados: list[EstadoHerramienta] = []
    for nombre, modulo in HERRAMIENTAS_CRITICAS.items():
        esperado = versiones.get(nombre)
        estados.append(_estado_herramienta(nombre, modulo, esperado))
    return tuple(estados)


def _estado_herramienta(nombre: str, modulo: str, esperado: str | None) -> EstadoHerramienta:
    comando = [sys.executable, "-m", modulo, "--version"]
    resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
    if resultado.returncode != 0:
        detalle = (resultado.stderr or resultado.stdout or "error desconocido").strip()
        return EstadoHerramienta(nombre, esperado, False, None, detalle)

    version = _extraer_version(resultado.stdout or resultado.stderr or "")
    return EstadoHerramienta(nombre, esperado, True, version, None)


def _extraer_version(texto: str) -> str | None:
    match = PATRON_VERSION.search(texto)
    if not match:
        return None
    return match.group("version")


def _lineas_herramienta(herramienta: EstadoHerramienta) -> list[str]:
    if not herramienta.instalada:
        return [
            f"[doctor][error] {herramienta.nombre}: NO disponible.",
            "[doctor][accion] Instala dependencias: python -m pip install -r requirements-dev.txt",
            f"[doctor][detalle] {herramienta.detalle_error or 'sin detalle'}",
        ]

    esperado = herramienta.version_esperada or "(sin pin detectado)"
    instalada = herramienta.version_instalada or "desconocida"
    if herramienta.version_esperada and herramienta.version_instalada != herramienta.version_esperada:
        return [
            f"[doctor][error] {herramienta.nombre}: versión desalineada (instalada={instalada}, pin={esperado}).",
            "[doctor][accion] Reinstala lock dev: python -m pip install -r requirements-dev.txt",
        ]

    return [f"[doctor] {herramienta.nombre}: OK (instalada={instalada}, pin={esperado})."]


def _lineas_ayuda(diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool) -> list[str]:
    if exigir_wheelhouse and not diagnostico.wheelhouse_disponible:
        return [
            "[doctor][error] Modo offline requerido y wheelhouse ausente.",
            "[doctor][accion] Define CLINICDESK_WHEELHOUSE o crea wheelhouse con:",
            "[doctor][accion] python -m scripts.dev.build_wheelhouse",
        ]
    if not diagnostico.wheelhouse_disponible:
        return [
            "[doctor][warn] Wheelhouse no disponible; setup dependerá de red/proxy.",
            "[doctor][accion] Opcional offline-first: python -m scripts.dev.build_wheelhouse",
        ]
    return ["[doctor] Wheelhouse listo para instalación offline-first."]
