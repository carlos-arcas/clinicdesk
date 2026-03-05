from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ruta_requirements = RAIZ_REPO / "requirements-dev.txt"
    if not ruta_requirements.exists():
        sys.stdout.write("[build_wheelhouse][error] No existe requirements-dev.txt\n")
        return 1

    wheelhouse = RAIZ_REPO / "wheelhouse"
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
    sys.stdout.write("[build_wheelhouse] Descargando dependencias dev en wheelhouse/\n")
    resultado = subprocess.run(comando, cwd=RAIZ_REPO, check=False)
    if resultado.returncode == 0:
        sys.stdout.write("[build_wheelhouse] OK\n")
        return 0

    sys.stdout.write("[build_wheelhouse][error] No se pudo construir wheelhouse.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
