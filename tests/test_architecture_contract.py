from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "clinicdesk" / "app"
ALLOWLIST_PATH = REPO_ROOT / "docs" / "architecture_allowlist.json"


@dataclass(frozen=True)
class ReglaArquitectura:
    nombre: str
    carpeta: str
    prefijos_prohibidos: tuple[str, ...]


REGLAS = (
    ReglaArquitectura(
        "domain_no_dependencias_altas",
        "domain",
        ("clinicdesk.app.application", "clinicdesk.app.infrastructure", "clinicdesk.app.ui", "clinicdesk.app.pages"),
    ),
    ReglaArquitectura(
        "application_no_infra_ui",
        "application",
        ("clinicdesk.app.infrastructure", "clinicdesk.app.ui", "clinicdesk.app.pages"),
    ),
    ReglaArquitectura("infrastructure_no_ui", "infrastructure", ("clinicdesk.app.ui", "clinicdesk.app.pages")),
    ReglaArquitectura("ui_no_domain_directo", "ui", ("clinicdesk.app.domain",)),
    ReglaArquitectura("pages_no_domain_directo", "pages", ("clinicdesk.app.domain",)),
)


def _cargar_allowlist() -> dict[tuple[str, str], set[str]]:
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    allowlist: dict[tuple[str, str], set[str]] = {}
    for item in payload.get("entries", []):
        allowlist[(item["rule"], item["path"])] = set(item.get("imports", []))
    return allowlist


def _modulos_importados(path_archivo: Path) -> list[str]:
    tree = ast.parse(path_archivo.read_text(encoding="utf-8"), filename=path_archivo.as_posix())
    modulos: list[str] = []
    for nodo in ast.walk(tree):
        if isinstance(nodo, ast.Import):
            modulos.extend(alias.name for alias in nodo.names)
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.append(nodo.module)
    return modulos


def _violaciones_regla(regla: ReglaArquitectura, allowlist: dict[tuple[str, str], set[str]]) -> list[str]:
    base = APP_ROOT / regla.carpeta
    violaciones: list[str] = []
    for archivo in sorted(base.rglob("*.py")):
        relativo = archivo.relative_to(REPO_ROOT).as_posix()
        permitidos = allowlist.get((regla.nombre, relativo), set())
        for modulo in _modulos_importados(archivo):
            if not any(modulo == p or modulo.startswith(f"{p}.") for p in regla.prefijos_prohibidos):
                continue
            if modulo in permitidos:
                continue
            violaciones.append(f"{regla.nombre}: {relativo} -> {modulo}")
    return violaciones


def test_contrato_de_arquitectura() -> None:
    allowlist = _cargar_allowlist()
    violaciones = [item for regla in REGLAS for item in _violaciones_regla(regla, allowlist)]
    assert not violaciones, "\n".join(["Se rompió el Architecture Contract:", *violaciones])
