"""Genera un release bundle en formato zip."""

from __future__ import annotations

import json
import os
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from clinicdesk import __version__

_RUTAS_OBLIGATORIAS = (
    Path("clinicdesk"),
    Path("scripts"),
    Path("requirements.txt"),
    Path("requirements-dev.txt"),
    Path("README.md"),
    Path("docs/security_hardening.md"),
    Path("docs/security_keys.md"),
)

_DIRECTORIOS_EXCLUIDOS = {
    ".venv",
    "__pycache__",
    "logs",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "data",
    "dist",
}
_EXT_EXCLUIDAS = {".pyc", ".sqlite", ".db"}


def _es_ruta_excluida(ruta_relativa: Path) -> bool:
    partes = set(ruta_relativa.parts)
    if _DIRECTORIOS_EXCLUIDOS.intersection(partes):
        return True
    return ruta_relativa.suffix in _EXT_EXCLUIDAS


def _iterar_archivos_fuente(raiz_repo: Path) -> list[Path]:
    archivos: list[Path] = []
    for ruta in _RUTAS_OBLIGATORIAS:
        ruta_absoluta = raiz_repo / ruta
        if not ruta_absoluta.exists():
            raise FileNotFoundError(f"No existe la ruta obligatoria para release: {ruta}")
        if ruta_absoluta.is_file():
            if not _es_ruta_excluida(ruta):
                archivos.append(ruta)
            continue
        for archivo in sorted(ruta_absoluta.rglob("*")):
            if not archivo.is_file():
                continue
            ruta_relativa = archivo.relative_to(raiz_repo)
            if _es_ruta_excluida(ruta_relativa):
                continue
            archivos.append(ruta_relativa)
    return sorted(set(archivos))


def _construir_manifest() -> dict[str, str]:
    return {
        "version": __version__,
        "git_sha": os.getenv("GITHUB_SHA", ""),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
    }


def construir_release_bundle(raiz_repo: Path | None = None) -> Path:
    """Construye el zip de distribución y devuelve su ruta."""
    repo = (raiz_repo or Path.cwd()).resolve()
    dist_dir = repo / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    zip_path = dist_dir / f"clinicdesk-{__version__}.zip"
    archivos = _iterar_archivos_fuente(repo)
    manifest = _construir_manifest()

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zipf:
        for ruta_relativa in archivos:
            zipf.write(repo / ruta_relativa, arcname=PurePosixPath(ruta_relativa.as_posix()))
        zipf.writestr("MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    return zip_path


def main() -> None:
    """Entrada CLI del generador de release bundle."""
    salida = construir_release_bundle()
    print(salida.as_posix())


if __name__ == "__main__":
    main()
