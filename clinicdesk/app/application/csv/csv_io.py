# application/csv/csv_io.py
"""Utilidades CSV reutilizables."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass(slots=True)
class CsvRowError:
    row_number: int
    message: str
    raw: Dict[str, str]


@dataclass(slots=True)
class CsvReadResult:
    headers: List[str]
    rows: List[Dict[str, str]]
    errors: List[CsvRowError]


def normalize_header(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "_")


def _detect_delimiter(sample: str) -> str:
    if not sample:
        return ","
    candidates = [",", ";", "\t", "|"]
    counts = {delimiter: sample.count(delimiter) for delimiter in candidates}
    return max(counts, key=counts.get) if max(counts.values()) > 0 else ","


def _open_text(path: Path):
    try:
        return path.open("r", encoding="utf-8-sig", newline="")
    except UnicodeDecodeError:
        return path.open("r", encoding="latin-1", newline="")


def _build_headers(fieldnames: Sequence[str] | None) -> tuple[list[str], dict[str, str]]:
    if fieldnames is None:
        return [], {}
    headers = [normalize_header(header) for header in fieldnames]
    header_map = {header: normalize_header(header) for header in fieldnames}
    return headers, header_map


def _normalize_required(required_headers: Optional[Sequence[str]]) -> list[str]:
    return [normalize_header(header) for header in (required_headers or [])]


def _missing_required(headers: list[str], required: list[str]) -> list[str]:
    return [header for header in required if header not in headers]


def _normalize_row(raw_row: dict[str, str] | None, header_map: dict[str, str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for key, value in (raw_row or {}).items():
        normalized_key = header_map.get(key, normalize_header(key))
        normalized[normalized_key] = (value or "").strip()
    return normalized


def read_csv(
    path: str | Path,
    *,
    required_headers: Optional[Sequence[str]] = None,
    allow_extra_headers: bool = True,
) -> CsvReadResult:
    p = Path(path)
    errors: List[CsvRowError] = []
    rows: List[Dict[str, str]] = []

    with _open_text(p) as file_handle:
        sample = file_handle.read(2048)
        file_handle.seek(0)

        reader = csv.DictReader(file_handle, delimiter=_detect_delimiter(sample))
        headers, header_map = _build_headers(reader.fieldnames)
        if not headers:
            return CsvReadResult(headers=[], rows=[], errors=[CsvRowError(1, "CSV sin cabecera.", {})])

        normalized_required = _normalize_required(required_headers)
        missing = _missing_required(headers, normalized_required)
        if missing:
            errors.append(CsvRowError(row_number=1, message=f"Faltan columnas obligatorias: {missing}", raw={}))

        rows.extend(_normalize_row(raw_row, header_map) for raw_row in reader)

    if required_headers and not allow_extra_headers:
        allowed = set(normalized_required)
        extra = [header for header in headers if header not in allowed]
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
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(headers), delimiter=delimiter)
        writer.writeheader()
        for r in rows:
            out = {h: ("" if r.get(h) is None else r.get(h)) for h in headers}
            writer.writerow(out)
