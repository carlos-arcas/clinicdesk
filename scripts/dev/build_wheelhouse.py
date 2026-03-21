from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.quality_gate_components.bootstrap_dependencias import diagnosticar_wheelhouse_desde_lock
from scripts.quality_gate_components.wheelhouse import resolver_wheelhouse

RAIZ_REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ruta_requirements = RAIZ_REPO / "requirements-dev.txt"
    if not ruta_requirements.exists():
        sys.stdout.write("[build_wheelhouse][error] No existe requirements-dev.txt\n")
        return 1

    wheelhouse = resolver_wheelhouse(RAIZ_REPO)
    wheelhouse.mkdir(parents=True, exist_ok=True)
    comando = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "-r",
        str(ruta_requirements),
        "-d",
        str(wheelhouse),
    ]
    sys.stdout.write(f"[build_wheelhouse] Descargando lock dev en {wheelhouse}\n")
    resultado = subprocess.run(comando, cwd=RAIZ_REPO, check=False)
    diagnostico = diagnosticar_wheelhouse_desde_lock(RAIZ_REPO, wheelhouse, ruta_requirements)
    if resultado.returncode == 0 and diagnostico.utilizable:
        sys.stdout.write(f"[build_wheelhouse] OK: {diagnostico.detalle}\n")
        return 0

    faltantes = ", ".join(diagnostico.paquetes_faltantes[:5])
    sufijo = f" Faltan al menos: {faltantes}." if faltantes else ""
    sys.stdout.write(f"[build_wheelhouse][error] Wheelhouse {diagnostico.codigo}: {diagnostico.detalle}.{sufijo}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
