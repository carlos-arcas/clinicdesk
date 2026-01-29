# application/csv/csv_io.py
"""
Utilidades CSV reutilizables.

Características:
- Auto-detección de delimitador (, ; \t)
- Lectura robusta (utf-8-sig, fallback latin-1)
- Normalización de headers
- Reporte de errores por fila
- Escritura consistente con headers definidos
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------


@dataclass(slots=True)
class CsvRowError:
    row_number: int          # 1-based (incluye cabecera como row 1)
    message: str
    raw: Dict[str, str]


@dataclass(slots=True)
class CsvReadResult:
    headers: List[str]
    rows: List[Dict[str, str]]
    errors: List[CsvRowError]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def normalize_header(name: str) -> str:
    """
    Normaliza nombres de columnas:
    - strip
    - lower
    - espacios -> _
    """
    return (name or "").strip().lower().replace(" ", "_")


def _detect_delimiter(sample: str) -> str:
    """
    Detección simple de delimitador. Prioriza ';' si aparece más que ','.
    """
    if not sample:
        return ","
    candidates = [",", ";", "\t", "|"]
    counts = {d: sample.count(d) for d in candidates}
    return max(counts, key=counts.get) if max(counts.values()) > 0 else ","


def _open_text(path: Path):
    """
    Abre texto con encoding robusto.
    """
    try:
        return path.open("r", encoding="utf-8-sig", newline="")
    except UnicodeDecodeError:
        return path.open("r", encoding="latin-1", newline="")


# ---------------------------------------------------------------------
# API
# ---------------------------------------------------------------------


def read_csv(
    path: str | Path,
    *,
    required_headers: Optional[Sequence[str]] = None,
    allow_extra_headers: bool = True,
) -> CsvReadResult:
    """
    Lee CSV y devuelve filas como dict(header->value string).

    required_headers:
    - lista de headers (normalizados) que deben existir
    allow_extra_headers:
    - si False, considera error si hay headers desconocidos (no usado normalmente)
    """
    p = Path(path)

    errors: List[CsvRowError] = []
    rows: List[Dict[str, str]] = []

    with _open_text(p) as f:
        sample = f.read(2048)
        f.seek(0)

        delimiter = _detect_delimiter(sample)
        reader = csv.DictReader(f, delimiter=delimiter)

        if reader.fieldnames is None:
            return CsvReadResult(headers=[], rows=[], errors=[CsvRowError(1, "CSV sin cabecera.", {})])

        headers = [normalize_header(h) for h in reader.fieldnames]
        header_map = {h: normalize_header(h) for h in reader.fieldnames}

        normalized_required = [normalize_header(h) for h in (required_headers or [])]

        missing = [h for h in normalized_required if h not in headers]
        if missing:
            errors.append(
                CsvRowError(
                    row_number=1,
                    message=f"Faltan columnas obligatorias: {missing}",
                    raw={},
                )
            )

        # Lectura filas
        for idx, raw_row in enumerate(reader, start=2):  # row 1 = header
            # Normaliza keys
            norm_row: Dict[str, str] = {}
            for k, v in (raw_row or {}).items():
                nk = header_map.get(k, normalize_header(k))
                norm_row[nk] = (v or "").strip()

            # Si hay required headers faltantes, ya se reportó arriba; aquí seguimos
            # para que el usuario vea el máximo de errores posible.

            rows.append(norm_row)

    # Control de extra headers si se necesita
    if required_headers and not allow_extra_headers:
        allowed = set(normalized_required)
        extra = [h for h in headers if h not in allowed]
        if extra:
            errors.append(CsvRowError(1, f"Columnas no permitidas: {extra}", {}))

    return CsvReadResult(headers=headers, rows=rows, errors=errors)


def write_csv(
    path: str | Path,
    *,
    headers: Sequence[str],
    rows: Iterable[Dict[str, object]],
    delimiter: str = ";",
) -> None:
    """
    Escribe CSV con headers dados (en ese orden).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(headers), delimiter=delimiter)
        writer.writeheader()
        for r in rows:
            out = {h: ("" if r.get(h) is None else r.get(h)) for h in headers}
            writer.writerow(out)
