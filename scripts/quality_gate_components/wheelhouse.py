from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re

PATRON_DIRECTIVA = re.compile(r"^(?:-r|--requirement)\s+(?P<ruta>.+)$")
PATRON_NORMALIZAR = re.compile(r"[-_.]+")
PATRON_WHEEL = re.compile(
    r"^(?P<nombre>.+?)-(?P<version>\d[^-]*)-(?P<resto>.+)\.whl$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EstadoWheelhouse:
    codigo: str
    detalle: str
    paquetes_faltantes: tuple[str, ...] = ()
    paquetes_cubiertos: tuple[str, ...] = ()
    wheels: tuple[str, ...] = ()
    requirements_lock: Path | None = None

    @property
    def utilizable(self) -> bool:
        return self.codigo == "utilizable"


@dataclass(frozen=True)
class PaqueteLock:
    nombre: str
    version: str


@dataclass(frozen=True)
class WheelArchivo:
    nombre: str
    version: str
    archivo: str


def normalizar_nombre_paquete(nombre: str) -> str:
    return PATRON_NORMALIZAR.sub("-", nombre).lower()


def resolver_wheelhouse(repo_root: Path) -> Path:
    ruta = os.environ.get("CLINICDESK_WHEELHOUSE")
    if ruta:
        return Path(ruta).expanduser().resolve()
    return repo_root / "wheelhouse"


def diagnosticar_wheelhouse(_repo_root: Path, wheelhouse: Path, requirements_lock: Path) -> EstadoWheelhouse:
    paquetes = _leer_paquetes_lock(requirements_lock)
    if not wheelhouse.exists():
        return EstadoWheelhouse("ausente", "directorio ausente", requirements_lock=requirements_lock)
    if not wheelhouse.is_dir():
        return EstadoWheelhouse(
            "invalido", "la ruta existe pero no es un directorio", requirements_lock=requirements_lock
        )
    wheels = _leer_wheels(wheelhouse)
    if not wheels:
        return EstadoWheelhouse("vacio", "el directorio no contiene archivos .whl", requirements_lock=requirements_lock)
    wheels_por_paquete = {wheel.nombre: wheel for wheel in wheels}
    faltantes: list[str] = []
    cubiertos: list[str] = []
    for paquete in paquetes:
        wheel = wheels_por_paquete.get(paquete.nombre)
        if wheel is None or wheel.version != paquete.version:
            faltantes.append(f"{paquete.nombre}=={paquete.version}")
            continue
        cubiertos.append(f"{paquete.nombre}=={paquete.version}")
    if faltantes:
        return EstadoWheelhouse(
            "incompleto",
            f"faltan {len(faltantes)} dependencias fijadas del lock",
            paquetes_faltantes=tuple(faltantes),
            paquetes_cubiertos=tuple(cubiertos),
            wheels=tuple(sorted(w.archivo for w in wheels)),
            requirements_lock=requirements_lock,
        )
    return EstadoWheelhouse(
        "utilizable",
        f"cubre {len(cubiertos)} dependencias fijadas del lock",
        paquetes_cubiertos=tuple(cubiertos),
        wheels=tuple(sorted(w.archivo for w in wheels)),
        requirements_lock=requirements_lock,
    )


def wheelhouse_disponible(repo_root: Path, wheelhouse: Path, requirements_lock: Path) -> bool:
    return diagnosticar_wheelhouse(repo_root, wheelhouse, requirements_lock).utilizable


def _leer_paquetes_lock(requirements_lock: Path) -> tuple[PaqueteLock, ...]:
    vistos: dict[str, PaqueteLock] = {}
    for ruta in _iterar_requirements(requirements_lock):
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            contenido = linea.strip()
            if not contenido or contenido.startswith("#"):
                continue
            if PATRON_DIRECTIVA.match(contenido):
                continue
            nombre, separador, version = contenido.partition("==")
            if separador != "==":
                continue
            vistos[normalizar_nombre_paquete(nombre)] = PaqueteLock(normalizar_nombre_paquete(nombre), version.strip())
    return tuple(vistos.values())


def _iterar_requirements(requirements_lock: Path) -> tuple[Path, ...]:
    pendientes = [requirements_lock]
    visitados: list[Path] = []
    while pendientes:
        actual = pendientes.pop(0)
        if actual in visitados:
            continue
        visitados.append(actual)
        for linea in actual.read_text(encoding="utf-8").splitlines():
            match = PATRON_DIRECTIVA.match(linea.strip())
            if not match:
                continue
            incluida = (actual.parent / match.group("ruta").strip()).resolve()
            pendientes.append(incluida)
    return tuple(visitados)


def _leer_wheels(wheelhouse: Path) -> tuple[WheelArchivo, ...]:
    wheels: dict[str, WheelArchivo] = {}
    for ruta in sorted(wheelhouse.glob("*.whl")):
        wheel = _parsear_wheel(ruta.name)
        if wheel is None:
            continue
        wheels[wheel.nombre] = wheel
    return tuple(wheels.values())


def _parsear_wheel(nombre_archivo: str) -> WheelArchivo | None:
    match = PATRON_WHEEL.match(nombre_archivo)
    if not match:
        return None
    return WheelArchivo(
        nombre=normalizar_nombre_paquete(match.group("nombre")),
        version=match.group("version"),
        archivo=nombre_archivo,
    )
