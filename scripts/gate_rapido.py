"""Gate rápido canónico del repositorio.

Este comando conserva un contrato estable (`python -m scripts.gate_rapido`)
y delega la ejecución al gate actual en modo rápido/report-only.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from scripts.quality_gate_components.ejecucion_canonica import (
    reejecutar_en_python_objetivo,
    renderizar_bloqueo,
    resolver_ejecucion_canonica,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGGER = logging.getLogger(__name__)


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("CLINICDESK_SANDBOX_MODE", "1")
    return env


def main() -> int:
    decision = resolver_ejecucion_canonica(REPO_ROOT, exigir_venv_repo=True)
    if decision.accion == "reejecutar":
        return reejecutar_en_python_objetivo(
            decision,
            ["-m", "scripts.gate_rapido", *sys.argv[1:]],
            env_extra={"CLINICDESK_SANDBOX_MODE": _build_env()["CLINICDESK_SANDBOX_MODE"]},
        )
    if decision.accion == "bloquear":
        for linea in renderizar_bloqueo(decision):
            sys.stderr.write(f"{linea}\n")
        return 1

    os.chdir(REPO_ROOT)
    comando = [
        sys.executable,
        "-m",
        "scripts.quality_gate_components.entrypoint",
        "--report-only",
    ]
    try:
        return subprocess.run(comando, check=False, env=_build_env()).returncode
    except OSError as exc:
        LOGGER.error("No se pudo ejecutar gate_rapido: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
