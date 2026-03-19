from __future__ import annotations

import re
from pathlib import Path

RUTAS_EXCLUIDAS = {
    ".git",
    ".venv",
    "build",
    "dist",
    "logs",
    "node_modules",
    "__pycache__",
}
PATRONES_STACK_PROHIBIDO = (
    re.compile(r"\bnext\.js\b", re.IGNORECASE),
    re.compile(r"\bdjango\b", re.IGNORECASE),
    re.compile(r"\breact\b", re.IGNORECASE),
    re.compile(r"\bvercel\b", re.IGNORECASE),
    re.compile(r"frontend web", re.IGNORECASE),
    re.compile(r"backend web", re.IGNORECASE),
    re.compile(r"\bspa\b"),
    re.compile(r"\bssr\b"),
    re.compile(r"\bssg\b"),
)
ALLOWLIST_REFERENCIAS = {
    Path("tests/guardrails/test_saneamiento_legacy_repo.py"),
}
ENTRYPOINTS_CANONICOS = (
    Path("scripts/run_app.py"),
    Path("scripts/setup.py"),
    Path("scripts/gate_rapido.py"),
    Path("scripts/gate_pr.py"),
)
RUTAS_LEGACY_PROHIBIDAS = (
    Path("presentacion/webapp"),
    Path("web/config"),
    Path("clinicdesk/app/pages/Nuevo documento de texto.txt"),
    Path("docs/proyecto_narrativo_features_10_bloqueo.md"),
    Path("PORTFOLIO.md"),
)
MARCADORES_PLACEHOLDER = (
    "[placeholder]",
    "lorem ipsum",
    "plantilla vacía",
    "template vacio",
)
ARCHIVOS_DOC = (".md", ".txt", ".rst")
ARCHIVOS_TEXTO = {".py", ".md", ".txt", ".json", ".toml", ".yml", ".yaml", ".sh", ".bat"}


def _ruta_excluida(path: Path) -> bool:
    return any(parte in RUTAS_EXCLUIDAS for parte in path.parts)


def _iterar_archivos_texto(repo_root: Path):
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if _ruta_excluida(rel):
            continue
        if rel in ALLOWLIST_REFERENCIAS:
            continue
        if path.suffix.lower() not in ARCHIVOS_TEXTO:
            continue
        yield rel


def test_no_reaparecen_referencias_a_stack_web_incorrecto() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    hallazgos: list[str] = []

    for rel in _iterar_archivos_texto(repo_root):
        contenido = (repo_root / rel).read_text(encoding="utf-8", errors="ignore").lower()
        for patron in PATRONES_STACK_PROHIBIDO:
            if patron.search(contenido):
                hallazgos.append(f"{rel}: contiene patron prohibido {patron.pattern!r}")

    assert not hallazgos, "\n".join(hallazgos)


def test_no_reaparecen_rutas_legacy_ni_docs_placeholder() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    existentes = [str(ruta) for ruta in RUTAS_LEGACY_PROHIBIDAS if (repo_root / ruta).exists()]
    assert not existentes, f"Se reintrodujeron residuos legacy: {existentes}"

    placeholders: list[str] = []
    for rel in _iterar_archivos_texto(repo_root):
        if rel.suffix.lower() not in ARCHIVOS_DOC:
            continue
        contenido = (repo_root / rel).read_text(encoding="utf-8", errors="ignore").lower()
        for marcador in MARCADORES_PLACEHOLDER:
            if marcador in contenido:
                placeholders.append(f"{rel}: contiene '{marcador}'")

    assert not placeholders, "\n".join(placeholders)


def test_entrypoints_canonicos_siguen_presentes() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    faltantes = [str(ruta) for ruta in ENTRYPOINTS_CANONICOS if not (repo_root / ruta).exists()]
    assert not faltantes, f"Faltan entrypoints canónicos: {faltantes}"
