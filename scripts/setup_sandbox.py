from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PYTHON_MINIMO = (3, 11)
RAIZ_REPO = Path(__file__).resolve().parents[1]


def _log(mensaje: str) -> None:
    sys.stdout.write(f"{mensaje}\n")


def _version_python_valida() -> bool:
    version_actual = sys.version_info
    if version_actual >= PYTHON_MINIMO:
        return True

    _log(
        "[setup_sandbox][error] Python incompatible: "
        f"{version_actual.major}.{version_actual.minor}. "
        f"Se requiere {PYTHON_MINIMO[0]}.{PYTHON_MINIMO[1]} o superior."
    )
    return False


def _texto_error_red(stderr: str) -> bool:
    patrones_red = (
        r"Temporary failure in name resolution",
        r"Failed to establish a new connection",
        r"Connection timed out",
        r"Read timed out",
        r"No route to host",
        r"Network is unreachable",
        r"ProxyError",
        r"407 Proxy Authentication Required",
    )
    return any(re.search(patron, stderr, flags=re.IGNORECASE) for patron in patrones_red)


def _instalar_archivo_requirements(nombre_archivo: str) -> bool:
    ruta_requirements = RAIZ_REPO / nombre_archivo
    if not ruta_requirements.exists():
        _log(f"[setup_sandbox][error] No existe {nombre_archivo} en {RAIZ_REPO}.")
        return False

    comando = [sys.executable, "-m", "pip", "install", "-r", str(ruta_requirements)]
    _log(f"[setup_sandbox] Instalando {nombre_archivo}...")
    resultado = subprocess.run(
        comando,
        cwd=RAIZ_REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    if resultado.returncode == 0:
        _log(f"[setup_sandbox] OK: {nombre_archivo}")
        return True

    stderr = (resultado.stderr or "").strip()
    stdout = (resultado.stdout or "").strip()
    if _texto_error_red(stderr):
        _log("[setup_sandbox][error] Falló la instalación por conectividad (sin internet/proxy).")
        _log(
            "[setup_sandbox][ayuda] Instala dependencias durante la fase de setup "
            "con acceso a red y reutiliza el entorno resultante en el runtime aislado."
        )
    else:
        _log(f"[setup_sandbox][error] pip devolvió exit code {resultado.returncode} al instalar {nombre_archivo}.")

    if stdout:
        _log("[setup_sandbox][stdout] Resumen de pip:")
        _log(stdout.splitlines()[-1])
    if stderr:
        _log("[setup_sandbox][stderr] Resumen de pip:")
        _log(stderr.splitlines()[-1])
    return False


def main() -> int:
    if not _version_python_valida():
        return 1

    archivos = ("requirements.txt", "requirements-dev.txt")
    resultados = [_instalar_archivo_requirements(nombre) for nombre in archivos]
    comando_sandbox = "CLINICDESK_SANDBOX_MODE=1 python -m scripts.gate_pr"
    if all(resultados):
        _log(f"[setup_sandbox] Entorno preparado. Ejecuta: {comando_sandbox}")
        return 0

    _log("[setup_sandbox] Setup incompleto. Revisa los mensajes y corrige antes del gate.")
    _log(f"[setup_sandbox][ayuda] Si estás en runtime aislado, prueba: {comando_sandbox}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
