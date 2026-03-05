from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from scripts.diagnostico_helpers import escribir_json, escribir_texto, primeras_lineas_redactadas
from scripts.quality_gate_components import config

_ENV_DIAGNOSTICO = "CLINICDESK_DIAGNOSTICO_PYTEST_255"
_MAX_LINEAS_RESUMEN = 120


def diagnostico_habilitado(entorno: dict[str, str] | None = None) -> bool:
    valor = (entorno or os.environ).get(_ENV_DIAGNOSTICO, "").strip()
    return valor == "1"


def ejecutar_diagnostico_pytest_255(
    *,
    comando: Sequence[str],
    resultado: subprocess.CompletedProcess[str],
    logs_dir: Path | None = None,
    max_lineas: int = _MAX_LINEAS_RESUMEN,
) -> dict[str, object]:
    directorio_logs = logs_dir or (config.REPO_ROOT / "logs")
    directorio_logs.mkdir(parents=True, exist_ok=True)

    stdout = resultado.stdout or ""
    stderr = resultado.stderr or ""
    escribir_texto(directorio_logs / "pytest_stdout.log", stdout)
    escribir_texto(directorio_logs / "pytest_stderr.log", stderr)

    resumen = _construir_resumen(comando=comando, resultado=resultado, max_lineas=max_lineas)
    destino_resumen = directorio_logs / "pytest_failure_summary.json"
    escribir_json(destino_resumen, resumen)
    return resumen


def _construir_resumen(
    *,
    comando: Sequence[str],
    resultado: subprocess.CompletedProcess[str],
    max_lineas: int,
) -> dict[str, object]:
    return {
        "returncode": resultado.returncode,
        "comando": list(comando),
        "stdout_lineas": primeras_lineas_redactadas(resultado.stdout or "", max_lineas=max_lineas),
        "stderr_lineas": primeras_lineas_redactadas(resultado.stderr or "", max_lineas=max_lineas),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    comando = [sys.executable, "-m", "pytest", *args.pytest_args]
    resultado = subprocess.run(comando, check=False, capture_output=True, text=True)
    if resultado.returncode == 255 and diagnostico_habilitado():
        ejecutar_diagnostico_pytest_255(comando=comando, resultado=resultado)
    sys.stdout.write(resultado.stdout or "")
    sys.stderr.write(resultado.stderr or "")
    return resultado.returncode


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta pytest y genera diagnóstico en fallo 255.")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Argumentos para pytest")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
