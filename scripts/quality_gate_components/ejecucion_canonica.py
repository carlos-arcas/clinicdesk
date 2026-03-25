from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys

from .toolchain import COMANDO_SETUP, cargar_interprete_esperado

MARCADOR_REEJECUCION = "CLINICDESK_REEJECUTADO_DESDE_VENV"
REASON_CODES_OPERATIVOS_CANONICO = ("VENV_REPO_NO_DISPONIBLE",)


@dataclass(frozen=True)
class DecisionEjecucionCanonica:
    accion: str
    python_objetivo: Path | None = None
    mensaje: tuple[str, ...] = ()



def contexto_ci() -> bool:
    return any(os.environ.get(nombre) for nombre in ("CI", "GITHUB_ACTIONS"))



def python_repo(repo_root: Path) -> Path:
    return cargar_interprete_esperado(repo_root).python_repo



def _python_actual() -> Path:
    return Path(sys.executable).resolve()



def _python_repo_utilizable(python_venv: Path) -> bool:
    return python_venv.exists() and os.access(python_venv, os.X_OK)



def resolver_ejecucion_canonica(repo_root: Path, *, exigir_venv_repo: bool) -> DecisionEjecucionCanonica:
    if os.environ.get(MARCADOR_REEJECUCION) == "1":
        return DecisionEjecucionCanonica("continuar")
    if contexto_ci():
        return DecisionEjecucionCanonica("continuar")

    python_venv = python_repo(repo_root)
    python_actual = _python_actual()
    if python_actual == python_venv.resolve():
        return DecisionEjecucionCanonica("continuar")
    if _python_repo_utilizable(python_venv):
        return DecisionEjecucionCanonica("reejecutar", python_objetivo=python_venv)
    if not exigir_venv_repo:
        return DecisionEjecucionCanonica("continuar")
    return DecisionEjecucionCanonica("bloquear", mensaje=_mensaje_bloqueo(repo_root, python_actual, python_venv))



def reejecutar_en_python_objetivo(decision: DecisionEjecucionCanonica, argv: list[str], *, env_extra: dict[str, str] | None = None) -> int:
    if decision.accion != "reejecutar" or decision.python_objetivo is None:
        raise RuntimeError("La decisión no requiere reejecución.")
    env = os.environ.copy()
    env[MARCADOR_REEJECUCION] = "1"
    if env_extra:
        env.update(env_extra)
    comando = [str(decision.python_objetivo), *argv]
    sys.stderr.write(f"[canonico] Reejecutando con el Python del repo: {decision.python_objetivo}\n")
    return subprocess.run(comando, check=False, env=env).returncode



def renderizar_bloqueo(decision: DecisionEjecucionCanonica) -> tuple[str, ...]:
    if decision.accion != "bloquear":
        return ()
    return decision.mensaje



def _mensaje_bloqueo(repo_root: Path, python_actual: Path, python_venv: Path) -> tuple[str, ...]:
    return (
        f"[canonico][reason_code] {REASON_CODES_OPERATIVOS_CANONICO[0]}",
        "[canonico][estado] Bloqueo operativo local: el proyecto todavía no se validó funcionalmente.",
        "[canonico][error] El comando canónico requiere el Python del .venv del repo y no puede usar el intérprete actual.",
        f"[canonico][error] Intérprete actual: {python_actual}",
        f"[canonico][error] Intérprete esperado: {python_venv}",
        f"[canonico][accion] Falta o no es ejecutable: {python_venv}",
        f"[canonico][accion] Crea o repara el entorno con: {COMANDO_SETUP}",
        "[canonico][accion] Si el bloqueo depende de red/proxy/wheelhouse, el setup y el doctor lo indicarán explícitamente antes del gate.",
        f"[canonico][accion] Tras reparar el entorno, reintenta el mismo comando desde {repo_root}.",
    )
