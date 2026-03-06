from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

RUTA_REPORTE_CALIDAD = Path("docs/quality_report.md")
RUTA_COBERTURA_JSON = Path("docs/coverage.json")
RUTA_COBERTURA_XML = Path("docs/coverage.xml")
RUTA_PIP_AUDIT = Path("docs/pip_audit_report.txt")
RUTA_SECRETS = Path("docs/secrets_scan_report.txt")
RUTA_RUFF_FORMAT_DIFF = Path("docs/ruff_format_diff.txt")
RUTA_SALIDA = Path("docs/pr_quality_gate_comment.md")

MARCADOR_COMENTARIO = "<!-- clinicdesk-quality-gate -->"
MAX_LINEAS_HEAD = 40
MAX_LINEAS_TAIL = 40

PATRONES_REDACTAR = [
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}\b"),
    re.compile(r"\b\d{8}[A-Za-z]\b"),
    re.compile(r"\b\d{2}[\s.-]?\d{3}[\s.-]?\d{3}[A-Za-z]\b"),
    re.compile(r"\b(?:sk|pk)_[A-Za-z0-9]{8,}\b"),
]


def redactar_texto(texto: str) -> str:
    redactado = texto
    for patron in PATRONES_REDACTAR:
        redactado = patron.sub("[REDACTED]", redactado)
    return redactado


def leer_lineas_head(path: Path, cantidad: int = MAX_LINEAS_HEAD) -> str:
    if not path.exists():
        return "(no encontrado)"
    lineas = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:cantidad]
    return redactar_texto("\n".join(lineas)) or "(vacío)"


def leer_lineas_tail(path: Path, cantidad: int = MAX_LINEAS_TAIL) -> str:
    if not path.exists():
        return "(no encontrado)"
    lineas = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return redactar_texto("\n".join(lineas[-cantidad:])) or "(vacío)"


def _extraer_porcentaje_json(candidatos: Iterable[object]) -> str | None:
    for valor in candidatos:
        if isinstance(valor, (int, float)):
            numero = float(valor)
            if 0 <= numero <= 1:
                numero *= 100
            if 0 <= numero <= 100:
                return f"{numero:.2f}%"
    return None


def cobertura_desde_json(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        datos = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return None

    if isinstance(datos, dict):
        candidatos = [
            datos.get("coverage"),
            datos.get("line_rate"),
            datos.get("total_coverage"),
            datos.get("percent_covered"),
            (datos.get("totals") or {}).get("percent_covered") if isinstance(datos.get("totals"), dict) else None,
        ]
        return _extraer_porcentaje_json(c for c in candidatos if c is not None)
    return None


def cobertura_desde_xml(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        raiz = ElementTree.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
    except ElementTree.ParseError:
        return None

    valor = raiz.attrib.get("line-rate") or raiz.attrib.get("line_rate")
    if valor is None:
        return None

    try:
        numero = float(valor)
    except ValueError:
        return None

    if 0 <= numero <= 1:
        numero *= 100
    if 0 <= numero <= 100:
        return f"{numero:.2f}%"
    return None


def obtener_cobertura() -> str:
    return cobertura_desde_json(RUTA_COBERTURA_JSON) or cobertura_desde_xml(RUTA_COBERTURA_XML) or "no disponible"


def generar_markdown(gate_outcome: str, run_url: str) -> str:
    quality_head = leer_lineas_head(RUTA_REPORTE_CALIDAD)
    pip_tail = leer_lineas_tail(RUTA_PIP_AUDIT)
    secrets_tail = leer_lineas_tail(RUTA_SECRETS)
    cobertura = obtener_cobertura()
    ruff_diff = "disponible" if RUTA_RUFF_FORMAT_DIFF.exists() else "no generado"

    return "\n".join(
        [
            MARCADOR_COMENTARIO,
            "## Quality Gate — Resumen automático",
            "",
            f"- **Outcome:** `{gate_outcome or 'unknown'}`",
            f"- **Run:** {run_url or '(no disponible)'}",
            f"- **Coverage:** `{cobertura}`",
            f"- **Ruff format diff artifact:** `{ruff_diff}`",
            "",
            "### quality_report.md (top 40 líneas)",
            "```text",
            quality_head,
            "```",
            "",
            "### pip-audit (tail 40 líneas)",
            "```text",
            pip_tail,
            "```",
            "",
            "### secrets scan (tail 40 líneas)",
            "```text",
            secrets_tail,
            "```",
        ]
    )


def main() -> int:
    gate_outcome = os.getenv("GATE_OUTCOME", "unknown")
    run_url = os.getenv("RUN_URL", "")
    contenido = generar_markdown(gate_outcome=gate_outcome, run_url=run_url)
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    RUTA_SALIDA.write_text(contenido + "\n", encoding="utf-8")
    logging.info("comentario_pr_quality_gate_generado", extra={"ruta": str(RUTA_SALIDA)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
