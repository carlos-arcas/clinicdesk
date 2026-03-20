from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
import os
import re
import subprocess
import sys

from .bootstrap_dependencias import resolver_wheelhouse, wheelhouse_disponible
from .toolchain import (
    COMANDO_BUILD_WHEELHOUSE,
    COMANDO_DOCTOR,
    COMANDO_GATE,
    COMANDO_REINSTALAR_LOCK,
    COMANDO_REGENERAR_LOCK,
    ErrorToolchain,
    HerramientaToolchain,
    ToolchainEsperado,
    cargar_toolchain_esperado,
)

PATRON_VERSION = re.compile(r"(?P<version>\d+\.\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class EstadoHerramienta:
    nombre: str
    version_esperada: str | None
    instalada: bool
    version_instalada: str | None
    detalle_error: str | None
    bloquea_gate: bool
    comando_corregir: str


@dataclass(frozen=True)
class DiagnosticoEntornoCalidad:
    python_activo: str
    venv_activo: bool
    cache_pip: str | None
    wheelhouse: Path
    wheelhouse_disponible: bool
    indice_pip: str | None
    proxy_configurado: bool
    diagnostico_red: str
    herramientas: tuple[EstadoHerramienta, ...]
    toolchain_error: str | None
    source_of_truth: str

    @property
    def tiene_faltantes(self) -> bool:
        return any(not herramienta.instalada for herramienta in self.herramientas)

    @property
    def tiene_desalineaciones(self) -> bool:
        return any(
            herramienta.instalada
            and herramienta.version_esperada is not None
            and herramienta.version_instalada != herramienta.version_esperada
            for herramienta in self.herramientas
        )

    @property
    def entorno_bloqueado(self) -> bool:
        return self.toolchain_error is not None or self.tiene_faltantes or self.tiene_desalineaciones


def diagnosticar_entorno_calidad(repo_root: Path, wheelhouse: Path | None = None) -> DiagnosticoEntornoCalidad:
    wheelhouse_path = resolver_wheelhouse(repo_root) if wheelhouse is None else wheelhouse
    indice_pip = _indice_pip()
    proxy_configurado = _proxy_configurado()
    diagnostico_red = _diagnostico_red(proxy_configurado, indice_pip, wheelhouse_path)
    try:
        toolchain = cargar_toolchain_esperado(repo_root)
        herramientas = _estado_herramientas(toolchain)
        toolchain_error = None
    except ErrorToolchain as exc:
        toolchain = None
        herramientas = ()
        toolchain_error = str(exc)

    return DiagnosticoEntornoCalidad(
        python_activo=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        venv_activo=_venv_activo(),
        cache_pip=_cache_pip(),
        wheelhouse=wheelhouse_path,
        wheelhouse_disponible=wheelhouse_disponible(wheelhouse_path),
        indice_pip=indice_pip,
        proxy_configurado=proxy_configurado,
        diagnostico_red=diagnostico_red,
        herramientas=herramientas,
        toolchain_error=toolchain_error,
        source_of_truth=_source_of_truth(toolchain, repo_root),
    )


def codigo_salida_estable(diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool = False) -> int:
    if diagnostico.toolchain_error is not None:
        return 5
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
        f"[doctor] Fuente de verdad tooling: {diagnostico.source_of_truth}",
        f"[doctor] Python activo: {diagnostico.python_activo}",
        f"[doctor] Venv activo: {'sí' if diagnostico.venv_activo else 'no'}",
        f"[doctor] pip cache dir: {diagnostico.cache_pip or 'no disponible'}",
        f"[doctor] pip index: {diagnostico.indice_pip or 'pip por defecto'}",
        f"[doctor] Proxy detectado: {'sí' if diagnostico.proxy_configurado else 'no'}",
        f"[doctor] Diagnóstico red: {diagnostico.diagnostico_red}",
        f"[doctor] Wheelhouse: {diagnostico.wheelhouse} ({'disponible' if diagnostico.wheelhouse_disponible else 'ausente'})",
    ]
    if diagnostico.toolchain_error is not None:
        lineas.extend(
            [
                f"[doctor][error] Toolchain esperado inválido: {diagnostico.toolchain_error}",
                f"[doctor][accion] Corrige/regenera el lock dev: {COMANDO_REGENERAR_LOCK}",
            ]
        )
    for herramienta in diagnostico.herramientas:
        lineas.extend(_lineas_herramienta(herramienta))
    lineas.extend(_lineas_ayuda(diagnostico, exigir_wheelhouse=exigir_wheelhouse))
    return lineas


def _source_of_truth(toolchain: ToolchainEsperado | None, repo_root: Path) -> str:
    requirements_dev_lock = toolchain.requirements_dev_lock if toolchain is not None else repo_root / "requirements-dev.txt"
    return f"{requirements_dev_lock.name} (versiones fijadas) + requirements-dev.in (entrada editable)"


def _venv_activo() -> bool:
    if os.environ.get("VIRTUAL_ENV"):
        return True
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _cache_pip() -> str | None:
    resultado = subprocess.run([sys.executable, "-m", "pip", "cache", "dir"], capture_output=True, text=True, check=False)
    if resultado.returncode != 0:
        return None
    valor = (resultado.stdout or "").strip()
    return valor or None


def _indice_pip() -> str | None:
    return os.environ.get("PIP_INDEX_URL") or os.environ.get("UV_INDEX_URL")


def _proxy_configurado() -> bool:
    return any(os.environ.get(nombre) for nombre in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"))


def _diagnostico_red(proxy_configurado: bool, indice_pip: str | None, wheelhouse: Path) -> str:
    if wheelhouse_disponible(wheelhouse):
        return "wheelhouse disponible: el setup puede instalar sin red si los wheels cubren el lock."
    if proxy_configurado or indice_pip:
        return "sin wheelhouse; la instalación dependerá de acceso al índice configurado/proxy."
    return "sin wheelhouse ni proxy/index explícito; una red restringida bloqueará la reinstalación."


def _estado_herramientas(toolchain: ToolchainEsperado) -> tuple[EstadoHerramienta, ...]:
    return tuple(_estado_herramienta(herramienta, toolchain.version_esperada(herramienta.nombre_paquete)) for herramienta in toolchain.herramientas)


def _estado_herramienta(herramienta: HerramientaToolchain, esperado: str | None) -> EstadoHerramienta:
    if herramienta.usar_metadata:
        return _estado_herramienta_por_metadata(herramienta, esperado)
    comando = [sys.executable, "-m", herramienta.modulo_python, *herramienta.comando_version]
    resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
    if resultado.returncode != 0:
        detalle = (resultado.stderr or resultado.stdout or "error desconocido").strip()
        return EstadoHerramienta(
            nombre=herramienta.nombre_paquete,
            version_esperada=esperado,
            instalada=False,
            version_instalada=None,
            detalle_error=detalle,
            bloquea_gate=True,
            comando_corregir=COMANDO_REINSTALAR_LOCK,
        )

    version = _extraer_version(resultado.stdout or resultado.stderr or "")
    desalineada = esperado is not None and version != esperado
    return EstadoHerramienta(
        nombre=herramienta.nombre_paquete,
        version_esperada=esperado,
        instalada=True,
        version_instalada=version,
        detalle_error=None,
        bloquea_gate=desalineada,
        comando_corregir=COMANDO_REINSTALAR_LOCK,
    )


def _estado_herramienta_por_metadata(herramienta: HerramientaToolchain, esperado: str | None) -> EstadoHerramienta:
    try:
        version = metadata.version(herramienta.nombre_paquete)
    except metadata.PackageNotFoundError:
        return EstadoHerramienta(
            nombre=herramienta.nombre_paquete,
            version_esperada=esperado,
            instalada=False,
            version_instalada=None,
            detalle_error="paquete no instalado en el intérprete activo",
            bloquea_gate=True,
            comando_corregir=COMANDO_REINSTALAR_LOCK,
        )
    return EstadoHerramienta(
        nombre=herramienta.nombre_paquete,
        version_esperada=esperado,
        instalada=True,
        version_instalada=version,
        detalle_error=None,
        bloquea_gate=esperado is not None and version != esperado,
        comando_corregir=COMANDO_REINSTALAR_LOCK,
    )


def _extraer_version(texto: str) -> str | None:
    match = PATRON_VERSION.search(texto)
    return None if not match else match.group("version")


def _lineas_herramienta(herramienta: EstadoHerramienta) -> list[str]:
    esperado = herramienta.version_esperada or "sin pin detectado"
    instalada = herramienta.version_instalada or "no instalada"
    if not herramienta.instalada:
        return [
            f"[doctor][error] {herramienta.nombre}: falta en el entorno; gate bloqueado.",
            f"[doctor][detalle] esperado={esperado}; error={herramienta.detalle_error or 'sin detalle'}",
            f"[doctor][accion] Ejecuta: {herramienta.comando_corregir}",
        ]
    if herramienta.version_esperada and herramienta.version_instalada != herramienta.version_esperada:
        return [
            f"[doctor][error] {herramienta.nombre}: versión desalineada; gate bloqueado.",
            f"[doctor][detalle] esperada={esperado}; instalada={instalada}",
            f"[doctor][accion] Ejecuta: {herramienta.comando_corregir}",
        ]
    return [f"[doctor] {herramienta.nombre}: OK (esperada={esperado}; instalada={instalada})."]


def _lineas_ayuda(diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool) -> list[str]:
    if exigir_wheelhouse and not diagnostico.wheelhouse_disponible:
        return [
            "[doctor][error] Modo offline requerido y wheelhouse ausente; gate local no es recuperable sin dependencias externas.",
            f"[doctor][accion] Genera o apunta un wheelhouse: {COMANDO_BUILD_WHEELHOUSE}",
        ]
    if diagnostico.toolchain_error is not None:
        return [f"[doctor][accion] Revalida el entorno con: {COMANDO_DOCTOR}"]
    if diagnostico.entorno_bloqueado:
        return [
            f"[doctor][warn] El gate real seguirá fallando por entorno hasta corregir lo anterior: {COMANDO_GATE}",
            f"[doctor][accion] Revalida sin instalar nada con: {COMANDO_DOCTOR}",
        ]
    if not diagnostico.wheelhouse_disponible:
        return [
            "[doctor][warn] Wheelhouse ausente: setup dependerá de red/proxy y puede fallar en entornos restringidos.",
            f"[doctor][accion] Si necesitas modo offline-first, prepara wheels con: {COMANDO_BUILD_WHEELHOUSE}",
        ]
    return ["[doctor] Wheelhouse listo para instalación offline-first."]
