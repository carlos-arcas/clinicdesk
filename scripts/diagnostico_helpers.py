from __future__ import annotations

import json
import re
from pathlib import Path

PATRONES_SENSIBLES: tuple[re.Pattern[str], ...] = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\d{8}[A-Za-z]\b"),
    re.compile(r"\b(?:\+?\d{1,3})?[ -]?(?:\d[ -]?){8,}\d\b"),
    re.compile(r"\b(?:sk|pk)_[A-Za-z0-9_-]+\b"),
)


def escribir_texto(destino: Path, contenido: str) -> None:
    destino.write_text(contenido, encoding="utf-8")


def escribir_json(destino: Path, datos: dict[str, object]) -> None:
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def primeras_lineas_redactadas(texto: str, *, max_lineas: int) -> list[str]:
    lineas = texto.splitlines()[:max_lineas]
    return [redactar_linea(linea) for linea in lineas]


def redactar_linea(linea: str) -> str:
    salida = linea
    for patron in PATRONES_SENSIBLES:
        salida = patron.sub("[REDACTED]", salida)
    return salida
