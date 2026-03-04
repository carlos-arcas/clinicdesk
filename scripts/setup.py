from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.quality_gate_components.requirements_pinning import recolectar_lineas_no_pinneadas


def _instalar_requerimientos(path: Path) -> int:
    comando = [sys.executable, "-m", "pip", "install", "-r", str(path)]
    return subprocess.run(comando, check=False).returncode


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    runtime = repo_root / "requirements.txt"
    dev = repo_root / "requirements-dev.txt"

    for archivo in (runtime, dev):
        if not archivo.exists():
            sys.stderr.write(f"[setup] Falta {archivo.name}\n")
            return 1
        no_pinneadas = recolectar_lineas_no_pinneadas(archivo)
        if no_pinneadas:
            sys.stderr.write(f"[setup] Aviso: {archivo.name} contiene líneas no pinneadas.\n")

    runtime_rc = _instalar_requerimientos(runtime)
    if runtime_rc != 0:
        return runtime_rc
    return _instalar_requerimientos(dev)


if __name__ == "__main__":
    raise SystemExit(main())
