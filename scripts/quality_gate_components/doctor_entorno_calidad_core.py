from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
import os
import re
import subprocess
import sys

from .bootstrap_dependencias import diagnosticar_wheelhouse_desde_lock
from .wheelhouse import resolver_wheelhouse
from .entorno_python import EstadoInterprete, diagnosticar_interprete, lineas_ayuda_interprete
from .toolchain import (
    COMANDO_BUILD_WHEELHOUSE,
    COMANDO_DOCTOR,
    COMANDO_GATE,
    COMANDO_REGENERAR_LOCK,
    COMANDO_REINSTALAR_LOCK,
    ErrorToolchain,
    HerramientaToolchain,
    ToolchainEsperado,
    cargar_interprete_esperado,
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
    interprete: EstadoInterprete
    cache_pip: str | None
    wheelhouse: Path
    wheelhouse_estado: str
    wheelhouse_disponible: bool
    wheelhouse_detalle: str
    wheelhouse_faltantes: tuple[str, ...]
    indice_pip: str | None
    proxy_configurado: bool
    diagnostico_red: str
    herramientas: tuple[EstadoHerramienta, ...]
    toolchain_error: str | None
    source_of_truth: str

    @property
    def python_activo(self) -> str:
        return self.interprete.python_activo

    @property
    def python_path(self) -> str:
        return self.interprete.python_path

    @property
    def venv_activo(self) -> bool:
        return self.interprete.venv_activo

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


@dataclass(frozen=True)
class ClasificacionBloqueoEntorno:
    reason_code: str
    categoria: str
    accion_sugerida: str
    detalle: str


def diagnosticar_entorno_calidad(repo_root: Path, wheelhouse: Path | None = None) -> DiagnosticoEntornoCalidad:
    wheelhouse_path = resolver_wheelhouse(repo_root) if wheelhouse is None else wheelhouse
    indice_pip = _indice_pip()
    proxy_configurado = _proxy_configurado()
    interprete = diagnosticar_interprete(cargar_interprete_esperado(repo_root))
    diagnostico_wheelhouse = diagnosticar_wheelhouse_desde_lock(repo_root, wheelhouse_path)
    diagnostico_red = _diagnostico_red(proxy_configurado, indice_pip, diagnostico_wheelhouse)
    try:
        toolchain = cargar_toolchain_esperado(repo_root)
        herramientas = _estado_herramientas(toolchain)
        toolchain_error = None
    except ErrorToolchain as exc:
        toolchain = None
        herramientas = ()
        toolchain_error = str(exc)

    return DiagnosticoEntornoCalidad(
        interprete=interprete,
        cache_pip=_cache_pip(),
        wheelhouse=wheelhouse_path,
        wheelhouse_estado=diagnostico_wheelhouse.codigo,
        wheelhouse_disponible=diagnostico_wheelhouse.utilizable,
        wheelhouse_detalle=diagnostico_wheelhouse.detalle,
        wheelhouse_faltantes=diagnostico_wheelhouse.paquetes_faltantes,
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


def clasificar_bloqueo_entorno(
    diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool = False
) -> ClasificacionBloqueoEntorno | None:
    if diagnostico.toolchain_error is not None:
        return ClasificacionBloqueoEntorno(
            reason_code="TOOLCHAIN_LOCK_INVALIDO",
            categoria="toolchain",
            accion_sugerida=COMANDO_REGENERAR_LOCK,
            detalle="El lock dev no es válido/coherente y el gate no puede validar el repositorio.",
        )
    if diagnostico.tiene_faltantes:
        return ClasificacionBloqueoEntorno(
            reason_code="DEPENDENCIAS_FALTANTES",
            categoria="toolchain",
            accion_sugerida=COMANDO_REINSTALAR_LOCK,
            detalle="Faltan herramientas del gate en el intérprete activo.",
        )
    if diagnostico.tiene_desalineaciones:
        return ClasificacionBloqueoEntorno(
            reason_code="TOOLCHAIN_DESALINEADO",
            categoria="toolchain",
            accion_sugerida=COMANDO_REINSTALAR_LOCK,
            detalle="Hay versiones desalineadas respecto a requirements-dev.txt.",
        )
    if exigir_wheelhouse and not diagnostico.wheelhouse_disponible:
        return ClasificacionBloqueoEntorno(
            reason_code="WHEELHOUSE_REQUERIDO_NO_DISPONIBLE",
            categoria="wheelhouse",
            accion_sugerida=COMANDO_BUILD_WHEELHOUSE,
            detalle="El modo offline está exigido y el wheelhouse no cubre el lock.",
        )
    if not diagnostico.wheelhouse_disponible and diagnostico.proxy_configurado:
        return ClasificacionBloqueoEntorno(
            reason_code="RED_PROXY_REQUERIDA_SIN_WHEELHOUSE",
            categoria="red_proxy",
            accion_sugerida=COMANDO_DOCTOR,
            detalle="Sin wheelhouse, la reinstalación depende de proxy/red y puede bloquearse.",
        )
    return None


def renderizar_reporte(diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool = False) -> list[str]:
    clasificacion = clasificar_bloqueo_entorno(diagnostico, exigir_wheelhouse=exigir_wheelhouse)
    interprete = diagnostico.interprete
    lineas = [
        "[doctor] Diagnóstico de entorno de calidad",
        f"[doctor] Fuente de verdad tooling: {diagnostico.source_of_truth}",
        f"[doctor] Python activo: {interprete.python_activo}",
        f"[doctor] Intérprete activo: {interprete.python_path}",
        f"[doctor] Python esperado repo: >= {interprete.version_minima_repo}",
        f"[doctor] Python esperado .venv: {interprete.python_esperado}",
        f"[doctor] Venv activo: {'sí' if interprete.venv_activo else 'no'}",
        f"[doctor] VIRTUAL_ENV: {interprete.venv_path or 'no definido'}",
        f"[doctor] Intérprete repo activo: {'sí' if interprete.usa_python_repo else 'no'}",
        f"[doctor] Compatibilidad Python: {'sí' if interprete.version_compatible else 'no'}",
        f"[doctor] Diagnóstico intérprete: {interprete.detalle}",
        f"[doctor] pip cache dir: {diagnostico.cache_pip or 'no disponible'}",
        f"[doctor] pip index: {diagnostico.indice_pip or 'pip por defecto'}",
        f"[doctor] Proxy detectado: {'sí' if diagnostico.proxy_configurado else 'no'}",
        f"[doctor] Diagnóstico red: {diagnostico.diagnostico_red}",
        f"[doctor] Wheelhouse: {diagnostico.wheelhouse} ({_estado_wheelhouse(diagnostico)})",
        f"[doctor] Wheelhouse detalle: {diagnostico.wheelhouse_detalle}",
    ]
    if clasificacion is not None:
        lineas.extend(
            [
                f"[doctor][reason_code] {clasificacion.reason_code}",
                f"[doctor][clasificacion] categoria={clasificacion.categoria}; detalle={clasificacion.detalle}",
                f"[doctor][accion] Siguiente paso sugerido: {clasificacion.accion_sugerida}",
            ]
        )
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
    requirements_dev_lock = (
        toolchain.requirements_dev_lock if toolchain is not None else repo_root / "requirements-dev.txt"
    )
    return f"{requirements_dev_lock.name} (versiones fijadas) + requirements-dev.in (entrada editable)"


def _cache_pip() -> str | None:
    resultado = subprocess.run(
        [sys.executable, "-m", "pip", "cache", "dir"], capture_output=True, text=True, check=False
    )
    if resultado.returncode != 0:
        return None
    valor = (resultado.stdout or "").strip()
    return valor or None


def _indice_pip() -> str | None:
    return os.environ.get("PIP_INDEX_URL") or os.environ.get("UV_INDEX_URL")


def _proxy_configurado() -> bool:
    return any(os.environ.get(nombre) for nombre in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"))


def _diagnostico_red(proxy_configurado: bool, indice_pip: str | None, diagnostico_wheelhouse) -> str:
    if diagnostico_wheelhouse.utilizable:
        return "wheelhouse utilizable: cubre el lock y el setup puede instalar sin red."
    if diagnostico_wheelhouse.codigo == "invalido":
        return "CLINICDESK_WHEELHOUSE apunta a una ruta inválida: existe pero no es un directorio utilizable."
    if diagnostico_wheelhouse.codigo in {"vacio", "incompleto"} and os.environ.get("CLINICDESK_WHEELHOUSE"):
        faltantes = ", ".join(diagnostico_wheelhouse.paquetes_faltantes[:3])
        sufijo = f" Faltan al menos: {faltantes}." if faltantes else ""
        return f"CLINICDESK_WHEELHOUSE está definido pero no cubre el lock completo.{sufijo}"
    if proxy_configurado and indice_pip:
        return "sin wheelhouse; la instalación dependerá del proxy y del índice configurado."
    if proxy_configurado:
        return "sin wheelhouse; la instalación dependerá del proxy configurado y de que el índice remoto responda."
    if indice_pip:
        return "sin wheelhouse; la instalación dependerá del índice configurado."
    return "sin wheelhouse ni proxy/index explícito; una red restringida bloqueará la reinstalación."


def _estado_herramientas(toolchain: ToolchainEsperado) -> tuple[EstadoHerramienta, ...]:
    return tuple(_estado_herramienta(h, toolchain.version_esperada(h.nombre_paquete)) for h in toolchain.herramientas)


def _estado_herramienta(herramienta: HerramientaToolchain, esperado: str | None) -> EstadoHerramienta:
    if herramienta.usar_metadata:
        return _estado_herramienta_por_metadata(herramienta, esperado)
    comando = [sys.executable, "-m", herramienta.modulo_python, *herramienta.comando_version]
    resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
    if resultado.returncode != 0:
        detalle = (resultado.stderr or resultado.stdout or "error desconocido").strip()
        return EstadoHerramienta(
            herramienta.nombre_paquete, esperado, False, None, detalle, True, COMANDO_REINSTALAR_LOCK
        )

    version = _extraer_version(resultado.stdout or resultado.stderr or "")
    desalineada = esperado is not None and version != esperado
    return EstadoHerramienta(
        herramienta.nombre_paquete, esperado, True, version, None, desalineada, COMANDO_REINSTALAR_LOCK
    )


def _estado_herramienta_por_metadata(herramienta: HerramientaToolchain, esperado: str | None) -> EstadoHerramienta:
    try:
        version = metadata.version(herramienta.nombre_paquete)
    except metadata.PackageNotFoundError:
        return EstadoHerramienta(
            herramienta.nombre_paquete,
            esperado,
            False,
            None,
            "paquete no instalado en el intérprete activo",
            True,
            COMANDO_REINSTALAR_LOCK,
        )
    return EstadoHerramienta(
        herramienta.nombre_paquete,
        esperado,
        True,
        version,
        None,
        esperado is not None and version != esperado,
        COMANDO_REINSTALAR_LOCK,
    )


def _extraer_version(texto: str) -> str | None:
    match = PATRON_VERSION.search(texto)
    return None if not match else match.group("version")


def _estado_wheelhouse(diagnostico: DiagnosticoEntornoCalidad) -> str:
    estados = {
        "utilizable": "utilizable",
        "incompleto": "incompleto",
        "vacio": "vacío",
        "invalido": "ruta inválida",
        "ausente": "ausente",
    }
    return estados.get(diagnostico.wheelhouse_estado, diagnostico.wheelhouse_estado)


def _lineas_herramienta(herramienta: EstadoHerramienta) -> list[str]:
    esperado = herramienta.version_esperada or "sin pin detectado"
    instalada = herramienta.version_instalada or "no instalada"
    if not herramienta.instalada:
        return [
            f"[doctor][error] {herramienta.nombre}: falta en el entorno; gate bloqueado.",
            f"[doctor][detalle] esperado={esperado}; instalada=no; error={herramienta.detalle_error or 'sin detalle'}",
            f"[doctor][accion] Ejecuta: {herramienta.comando_corregir}",
        ]
    if herramienta.version_esperada and herramienta.version_instalada != herramienta.version_esperada:
        return [
            f"[doctor][error] {herramienta.nombre}: versión desalineada; gate bloqueado.",
            f"[doctor][detalle] esperada={esperado}; instalada={instalada}; interprete_activo={sys.executable}",
            f"[doctor][accion] Ejecuta: {herramienta.comando_corregir}",
        ]
    return [f"[doctor] {herramienta.nombre}: OK (esperada={esperado}; instalada={instalada})."]


def _lineas_ayuda(diagnostico: DiagnosticoEntornoCalidad, exigir_wheelhouse: bool) -> list[str]:
    lineas = lineas_ayuda_interprete(diagnostico.interprete)
    if exigir_wheelhouse and not diagnostico.wheelhouse_disponible:
        faltantes = ", ".join(diagnostico.wheelhouse_faltantes[:5])
        detalle = f" Faltan al menos: {faltantes}." if faltantes else ""
        lineas.extend(
            [
                f"[doctor][error] Modo offline requerido y wheelhouse {diagnostico.wheelhouse_estado}; gate local no es recuperable sin dependencias externas.{detalle}",
                f"[doctor][accion] Genera o apunta un wheelhouse válido: {COMANDO_BUILD_WHEELHOUSE}",
            ]
        )
        return lineas
    if diagnostico.toolchain_error is not None:
        lineas.append(f"[doctor][accion] Revalida el entorno con: {COMANDO_DOCTOR}")
        return lineas
    if diagnostico.entorno_bloqueado:
        lineas.extend(
            [
                f"[doctor][warn] El gate real seguirá fallando por entorno hasta corregir lo anterior: {COMANDO_GATE}",
                f"[doctor][accion] Revalida sin instalar nada con: {COMANDO_DOCTOR}",
            ]
        )
        return lineas
    if not diagnostico.wheelhouse_disponible:
        lineas.extend(
            [
                "[doctor][warn] Wheelhouse ausente o incompleto: setup dependerá de red/proxy y puede fallar en entornos restringidos.",
                f"[doctor][accion] Si necesitas modo offline-first, prepara wheels con: {COMANDO_BUILD_WHEELHOUSE}",
            ]
        )
        return lineas
    lineas.append("[doctor] Wheelhouse listo para instalación offline-first.")
    return lineas
