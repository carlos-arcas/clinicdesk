from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.quality_gate_components.bootstrap_dependencias import (
    comando_instalacion,
    diagnosticar_wheelhouse_desde_lock,
)
from scripts.quality_gate_components.wheelhouse import resolver_wheelhouse
from scripts.quality_gate_components.doctor_entorno_calidad_core import (
    codigo_salida_estable,
    diagnosticar_entorno_calidad,
    renderizar_reporte,
)
from scripts.quality_gate_components.ejecucion_canonica import (
    reejecutar_en_python_objetivo,
    resolver_ejecucion_canonica,
)
from scripts.quality_gate_components.toolchain import COMANDO_DOCTOR, COMANDO_GATE


@dataclass(frozen=True)
class DiagnosticoInstalacion:
    categoria: str
    detalle: str
    accion: str


def resolve_repo_root() -> Path:
    override = os.environ.get("CLINICDESK_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = resolve_repo_root()
VENV_DIR = PROJECT_ROOT / ".venv"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _log(mensaje: str) -> None:
    sys.stdout.write(f"{mensaje}\n")


def _resumen_error_instalacion(stderr: str, stdout: str, *, wheelhouse: Path | None = None) -> list[str]:
    diagnostico = _clasificar_error_instalacion(
        stderr, stdout, wheelhouse=wheelhouse or resolver_wheelhouse(PROJECT_ROOT)
    )
    if diagnostico is None:
        return []
    return [
        f"[setup][diagnostico] {diagnostico.detalle}",
        f"[setup][accion] {diagnostico.accion}",
    ]


def _clasificar_error_instalacion(stderr: str, stdout: str, *, wheelhouse: Path) -> DiagnosticoInstalacion | None:
    texto = f"{stdout}\n{stderr}".lower()
    diagnostico_wheelhouse = diagnosticar_wheelhouse_desde_lock(PROJECT_ROOT, wheelhouse)
    offline = diagnostico_wheelhouse.utilizable
    if any(
        token in texto for token in ("proxyerror", "407 proxy", "tunnel connection failed", "cannot connect to proxy")
    ):
        return DiagnosticoInstalacion(
            "proxy",
            "Fallo de red/proxy detectado durante instalación.",
            "Revisa HTTP_PROXY/HTTPS_PROXY, valida el índice configurado o usa un wheelhouse accesible antes de reintentar.",
        )
    if any(
        token in texto
        for token in (
            "temporary failure in name resolution",
            "failed to establish a new connection",
            "connection timed out",
            "name or service not known",
        )
    ):
        accion = "Sin wheelhouse ni acceso a red, este entorno no es recuperable localmente."
        if offline:
            accion = f"El wheelhouse existe en {wheelhouse}; revisa cobertura del lock. Faltan al menos: {', '.join(diagnostico_wheelhouse.paquetes_faltantes[:3]) or 'sin detalle'}."
        return DiagnosticoInstalacion("red", "Fallo de conectividad a índices Python detectado.", accion)
    if "no matching distribution found" in texto or "could not find a version that satisfies the requirement" in texto:
        return DiagnosticoInstalacion(
            "version",
            "El lock pide una versión que pip no pudo resolver con el índice actual o con el intérprete activo.",
            "Verifica versión de Python, índice/proxy y que requirements-dev.txt esté regenerado antes de reintentar.",
        )
    if any(token in texto for token in ("hashes are required", "do not match the hashes", "hash mismatch")):
        return DiagnosticoInstalacion(
            "lock",
            "Se detectó incoherencia entre el lock y el artefacto descargado.",
            "Regenera el lock o limpia artefactos/cache inconsistentes antes de reinstalar.",
        )
    if any(
        token in texto
        for token in (
            "no such file or directory",
            "invalid wheel filename",
            "is not a supported wheel on this platform",
        )
    ):
        return DiagnosticoInstalacion(
            "wheelhouse",
            "El wheelhouse/configuración local no contiene wheels utilizables para este intérprete/plataforma.",
            "Revisa CLINICDESK_WHEELHOUSE y reconstruye wheels compatibles si necesitas modo offline-first.",
        )
    if "--no-index" in texto and not offline:
        return DiagnosticoInstalacion(
            "wheelhouse-ausente",
            "Se intentó modo offline-first pero el wheelhouse no está disponible.",
            "Define CLINICDESK_WHEELHOUSE con una ruta válida o usa red/proxy reales para instalar.",
        )
    return None


def _run_command(command: list[str], descripcion: str, *, wheelhouse: Path | None = None) -> None:
    _log(f"[setup] {descripcion}: {' '.join(command)}")
    resultado = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    if resultado.stdout:
        _log(resultado.stdout.rstrip())
    if resultado.stderr:
        _log(resultado.stderr.rstrip())
    if resultado.returncode != 0:
        pistas = _resumen_error_instalacion(
            resultado.stderr or "",
            resultado.stdout or "",
            wheelhouse=wheelhouse or resolver_wheelhouse(PROJECT_ROOT),
        )
        detalle = f"Fallo '{descripcion}' (exit code {resultado.returncode})."
        if pistas:
            detalle = (
                f"{detalle} "
                f"{' '.join(linea.replace('[setup][diagnostico] ', '').replace('[setup][accion] ', '') for linea in pistas)}"
            )
        raise RuntimeError(detalle)


def _log_contexto_interprete() -> None:
    _log(f"[setup] Python lanzador actual: {sys.executable}")
    _log(f"[setup] Repo root: {PROJECT_ROOT}")
    _log(f"[setup] Venv esperado del repo: {_venv_python()}")


def _crear_venv_si_no_existe() -> None:
    if VENV_DIR.exists():
        _log(f"[setup] Entorno virtual ya existe en {VENV_DIR}")
        return
    _run_command([sys.executable, "-m", "venv", str(VENV_DIR)], "Crear entorno virtual .venv")


def _requirements_con_rango(requirements_path: Path) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for numero_linea, linea in enumerate(requirements_path.read_text(encoding="utf-8").splitlines(), start=1):
        contenido = linea.strip()
        if not contenido or contenido.startswith("#") or contenido.startswith(("-", "--")):
            continue
        if "==" not in contenido:
            offenders.append((numero_linea, contenido))
    return offenders


def _advertir_requirements_no_pinneados() -> None:
    for nombre in ("requirements.txt", "requirements-dev.txt"):
        ruta = PROJECT_ROOT / nombre
        if not ruta.exists():
            continue
        offenders = _requirements_con_rango(ruta)
        if not offenders:
            continue
        _log(f"[setup][warn] {nombre} contiene entradas sin pin estricto (==):")
        for numero_linea, contenido in offenders:
            _log(f"[setup][warn]   - linea {numero_linea}: {contenido}")


def _instalar_dependencias(python_venv: Path) -> None:
    requirements = PROJECT_ROOT / "requirements.txt"
    requirements_dev = PROJECT_ROOT / "requirements-dev.txt"
    if not requirements.exists() or not requirements_dev.exists():
        raise RuntimeError("No se encontraron requirements.txt y/o requirements-dev.txt en la raíz del repositorio.")

    wheelhouse = resolver_wheelhouse(PROJECT_ROOT)
    diagnostico_wheelhouse = diagnosticar_wheelhouse_desde_lock(PROJECT_ROOT, wheelhouse)
    if os.environ.get("CLINICDESK_WHEELHOUSE") and not diagnostico_wheelhouse.utilizable:
        faltantes = ", ".join(diagnostico_wheelhouse.paquetes_faltantes[:5])
        sufijo = f" Faltan al menos: {faltantes}." if faltantes else ""
        raise RuntimeError(
            f"CLINICDESK_WHEELHOUSE apunta a {wheelhouse}, pero está {diagnostico_wheelhouse.codigo}: "
            f"{diagnostico_wheelhouse.detalle}.{sufijo} Ajusta la ruta, corrige el proxy/red para construirlo, "
            "o regenera el wheelhouse antes de reintentar."
        )
    comando_runtime, modo_runtime = comando_instalacion(str(python_venv), requirements, wheelhouse, PROJECT_ROOT)
    comando_dev, modo_dev = comando_instalacion(str(python_venv), requirements_dev, wheelhouse, PROJECT_ROOT)
    if diagnostico_wheelhouse.utilizable:
        _log(
            f"[setup] Wheelhouse utilizable en {wheelhouse}; cubre requirements-dev.txt y la instalación offline-first queda habilitada."
        )
    else:
        _log(
            f"[setup][warn] Wheelhouse {diagnostico_wheelhouse.codigo} en {wheelhouse}: {diagnostico_wheelhouse.detalle}. "
            "La instalación dependerá de red/proxy reales."
        )
    _run_command(comando_runtime, f"Instalar dependencias runtime ({modo_runtime})", wheelhouse=wheelhouse)
    _run_command(comando_dev, f"Instalar dependencias dev ({modo_dev})", wheelhouse=wheelhouse)


def _verificar_herramientas(python_venv: Path) -> None:
    verificaciones = [
        ("ruff", [str(python_venv), "-m", "ruff", "--version"]),
        ("pytest", [str(python_venv), "-m", "pytest", "--version"]),
        ("pip-audit", [str(python_venv), "-m", "pip_audit", "--version"]),
        ("mypy", [str(python_venv), "-m", "mypy", "--version"]),
    ]
    for nombre, comando in verificaciones:
        _run_command(comando, f"Verificar herramienta {nombre}")


def main() -> int:
    try:
        _log_contexto_interprete()
        decision = resolver_ejecucion_canonica(PROJECT_ROOT, exigir_venv_repo=False)
        if decision.accion == "reejecutar":
            return reejecutar_en_python_objetivo(decision, ["scripts/setup.py", *sys.argv[1:]])
        if decision.accion == "continuar" and not _venv_python().exists():
            _log(
                "[setup] .venv ausente o no utilizable todavía; se intentará crear/reparar con el Python lanzador actual."
            )

        diagnostico = diagnosticar_entorno_calidad(PROJECT_ROOT)
        for linea in renderizar_reporte(diagnostico):
            _log(linea)
        if not diagnostico.interprete.version_compatible:
            raise RuntimeError(
                "El Python lanzador no cumple la versión mínima del repo. "
                f"Usa {diagnostico.interprete.comando_recrear} con un Python >= {diagnostico.interprete.version_minima_repo}."
            )
        _crear_venv_si_no_existe()
        python_venv = _venv_python()
        if not python_venv.exists():
            raise RuntimeError(f"No se encontró el Python del venv: {python_venv}")
        _advertir_requirements_no_pinneados()
        _instalar_dependencias(python_venv)
        _verificar_herramientas(python_venv)
        diagnostico_final = diagnosticar_entorno_calidad(PROJECT_ROOT)
        if codigo_salida_estable(diagnostico_final) != 0:
            raise RuntimeError(
                "El entorno quedó desalineado tras setup. "
                f"Ejecuta {COMANDO_DOCTOR} para el detalle y no lances {COMANDO_GATE} hasta corregirlo."
            )
    except RuntimeError as exc:
        _log(f"[setup][error] {exc}")
        return 1

    _log(f"[setup] Entorno listo. Activa el venv con: {diagnostico_final.interprete.comando_activar}")
    _log(f"[setup] Próximos pasos: {COMANDO_DOCTOR} && {COMANDO_GATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
