from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.date_utils import parse_iso_date


CSV_COLUMNS = [
    "tipo_documento",
    "documento",
    "nombre",
    "apellidos",
    "telefono",
    "email",
    "fecha_nacimiento",
    "direccion",
    "activo",
    "num_historia",
    "alergias",
    "observaciones",
]


def export_csv(path: Path, pacientes: Iterable[Paciente]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for paciente in pacientes:
            payload = paciente.to_dict()
            payload.pop("id", None)
            writer.writerow(payload)


def import_csv(path: Path, create_paciente) -> int:
    count = 0
    with path.open("r", newline="", encoding="utf-8") as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            create_paciente(_paciente_from_csv(row))
            count += 1
    return count


def _paciente_from_csv(row: dict[str, str]) -> Paciente:
    return Paciente(
        tipo_documento=TipoDocumento(row["tipo_documento"]),
        documento=row["documento"],
        nombre=row["nombre"],
        apellidos=row["apellidos"],
        telefono=row.get("telefono") or None,
        email=row.get("email") or None,
        fecha_nacimiento=parse_iso_date(row.get("fecha_nacimiento") or None),
        direccion=row.get("direccion") or None,
        activo=bool(int(row.get("activo", "1"))),
        num_historia=None,
        alergias=row.get("alergias") or None,
        observaciones=row.get("observaciones") or None,
    )
