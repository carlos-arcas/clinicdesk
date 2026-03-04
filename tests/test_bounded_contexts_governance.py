from __future__ import annotations

import ast
import json
from pathlib import Path

from clinicdesk.app.application.contextos import Contexto, resolver_contexto_de_ruta


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "clinicdesk" / "app" / "application"
ALLOWLIST_PATH = REPO_ROOT / "docs" / "bounded_contexts_allowlist.json"

REGLAS_PROHIBIDAS: dict[tuple[str, str], str] = {
    (Contexto.PACIENTES.value, Contexto.ML_DEMO.value): "pacientes_no_importa_ml_demo",
    (Contexto.PACIENTES.value, Contexto.EXPORT.value): "pacientes_no_importa_export",
    (Contexto.EXPORT.value, Contexto.ML_DEMO.value): "export_no_importa_ml_demo",
    (Contexto.AUDITORIA_SEGURIDAD.value, Contexto.CITAS.value): "auditoria_no_importa_citas",
    (Contexto.AUDITORIA_SEGURIDAD.value, Contexto.PACIENTES.value): "auditoria_no_importa_pacientes",
    (Contexto.AUDITORIA_SEGURIDAD.value, Contexto.ML_DEMO.value): "auditoria_no_importa_ml_demo",
    (Contexto.AUDITORIA_SEGURIDAD.value, Contexto.EXPORT.value): "auditoria_no_importa_export",
    (Contexto.AUDITORIA_SEGURIDAD.value, Contexto.PREFERENCIAS.value): "auditoria_no_importa_preferencias",
    (Contexto.ML_DEMO.value, Contexto.CITAS.value): "ml_demo_no_importa_citas",
}


def _cargar_allowlist() -> set[tuple[str, str, str]]:
    if not ALLOWLIST_PATH.exists():
        return set()
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    return {
        (entry["regla"], entry["origen"], entry["destino"])
        for entry in entries
        if {"regla", "origen", "destino"}.issubset(entry)
    }


def _imports_modulo(path_archivo: Path) -> list[str]:
    modulo = ast.parse(path_archivo.read_text(encoding="utf-8"), filename=path_archivo.as_posix())
    imports: list[str] = []
    for nodo in ast.walk(modulo):
        if isinstance(nodo, ast.Import):
            imports.extend(alias.name for alias in nodo.names)
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            imports.append(nodo.module)
    return imports


def _iterar_violaciones() -> list[str]:
    allowlist = _cargar_allowlist()
    violaciones: list[str] = []
    for archivo in APP_ROOT.rglob("*.py"):
        origen = archivo.relative_to(REPO_ROOT).as_posix()
        contexto_origen = resolver_contexto_de_ruta(origen)
        if contexto_origen == Contexto.COMPARTIDO.value:
            continue
        for modulo in _imports_modulo(archivo):
            if not modulo.startswith("clinicdesk.app.application"):
                continue
            contexto_destino = resolver_contexto_de_ruta(modulo)
            regla = REGLAS_PROHIBIDAS.get((contexto_origen, contexto_destino))
            if not regla:
                continue
            fingerprint = (regla, origen, modulo)
            if fingerprint in allowlist:
                continue
            violaciones.append(f"{regla}: {origen} -> {modulo}")
    return violaciones


def test_gobernanza_bounded_contexts() -> None:
    violaciones = _iterar_violaciones()
    assert not violaciones, "Imports cruzados prohibidos entre contextos:\n" + "\n".join(sorted(violaciones))
