from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from scripts.quality_gate_components import config

_ENV_DIAGNOSTICO = "CLINICDESK_DIAGNOSTICO_PYTEST_255"
_MAX_LINEAS_RESUMEN = 120
_PATRONES_PII: tuple[re.Pattern[str], ...] = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\d{8}[A-Za-z]\b"),
    re.compile(r"\b(?:\+?\d{1,3})?[ -]?(?:\d[ -]?){8,}\d\b"),
)


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
    _escribir_log(directorio_logs / "pytest_stdout.log", stdout)
    _escribir_log(directorio_logs / "pytest_stderr.log", stderr)

    resumen = _construir_resumen(comando=comando, resultado=resultado, max_lineas=max_lineas)
    destino_resumen = directorio_logs / "pytest_failure_summary.json"
    destino_resumen.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


def _escribir_log(destino: Path, contenido: str) -> None:
    destino.write_text(contenido, encoding="utf-8")


def _construir_resumen(
    *,
    comando: Sequence[str],
    resultado: subprocess.CompletedProcess[str],
    max_lineas: int,
) -> dict[str, object]:
    return {
        "returncode": resultado.returncode,
        "comando": list(comando),
        "stdout_lineas": _normalizar_lineas(resultado.stdout or "", max_lineas=max_lineas),
        "stderr_lineas": _normalizar_lineas(resultado.stderr or "", max_lineas=max_lineas),
    }


def _normalizar_lineas(texto: str, *, max_lineas: int) -> list[str]:
    lineas = texto.splitlines()
    if len(lineas) > max_lineas:
        lineas = lineas[-max_lineas:]
    return [_redactar_linea(linea) for linea in lineas]


def _redactar_linea(linea: str) -> str:
    salida = linea
    for patron in _PATRONES_PII:
        salida = patron.sub("[REDACTED]", salida)
    return salida


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
