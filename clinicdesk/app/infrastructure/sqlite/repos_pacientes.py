# infrastructure/sqlite/repos_pacientes.py
"""
Repositorio SQLite para Pacientes.

Responsabilidades:
- CRUD de pacientes
- Búsquedas con filtros múltiples
- Conversión fila <-> modelo de dominio
- Base para import/export CSV

No contiene:
- Lógica de UI
- Validaciones de negocio complejas
- Código de bootstrap
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date


logger = logging.getLogger(__name__)


class _PacientesConsultasSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def list_all(self, *, solo_activos: bool = True) -> List[Paciente]:
        sql = "SELECT * FROM pacientes"
        if solo_activos:
            sql += " WHERE activo = 1"
        sql += " ORDER BY apellidos, nombre"
        try:
            rows = self._con.execute(sql).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesRepository.list_all: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Paciente]:
        clauses, params = self._build_search_filters(texto, tipo_documento, documento, activo)
        sql = "SELECT * FROM pacientes"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre"
        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesRepository.search: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def get_by_id(self, paciente_id: int) -> Optional[Paciente]:
        row = self._con.execute(
            "SELECT * FROM pacientes WHERE id = ?",
            (paciente_id,),
        ).fetchone()
        return self._row_to_model(row) if row else None

    def get_id_by_documento(
        self,
        tipo_documento: TipoDocumento | str,
        documento: str,
    ) -> Optional[int]:
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        row = self._con.execute(
            "SELECT id FROM pacientes WHERE tipo_documento = ? AND documento = ?",
            (tipo, documento),
        ).fetchone()
        return int(row["id"]) if row else None

    def _build_search_filters(
        self,
        texto: Optional[str],
        tipo_documento: Optional[TipoDocumento],
        documento: Optional[str],
        activo: Optional[bool],
    ) -> tuple[list[str], list[object]]:
        texto = normalize_search_text(texto)
        documento = normalize_search_text(documento)
        tipo_documento_value = normalize_search_text(tipo_documento.value if tipo_documento else None)
        clauses: list[str] = []
        params: list[object] = []

        if texto:
            clauses.append(
                "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
                "OR documento LIKE ? COLLATE NOCASE)"
            )
            like = like_value(texto)
            params.extend([like, like, like])

        if tipo_documento_value:
            clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo_documento_value))

        if documento:
            clauses.append("documento LIKE ? COLLATE NOCASE")
            params.append(like_value(documento))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        return clauses, params

    def _row_to_model(self, row: sqlite3.Row) -> Paciente:
        return Paciente(
            id=row["id"],
            tipo_documento=TipoDocumento(row["tipo_documento"]),
            documento=row["documento"],
            nombre=row["nombre"],
            apellidos=row["apellidos"],
            telefono=row["telefono"],
            email=row["email"],
            fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
            direccion=row["direccion"],
            activo=bool(row["activo"]),
            num_historia=row["num_historia"],
            alergias=row["alergias"],
            observaciones=row["observaciones"],
        )


class _PacientesCsvSqlite:
    _FIELDNAMES = [
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

    def export_csv(self, path: Path, pacientes: Iterable[Paciente]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=self._FIELDNAMES)
            writer.writeheader()
            for paciente in pacientes:
                row = paciente.to_dict()
                row.pop("id", None)
                writer.writerow(row)

    def import_csv(self, path: Path) -> list[Paciente]:
        pacientes: list[Paciente] = []
        with path.open("r", newline="", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                pacientes.append(self._row_to_paciente(row))
        return pacientes

    def _row_to_paciente(self, row: dict[str, str]) -> Paciente:
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


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class PacientesRepository:
    """Repositorio de acceso a datos para pacientes."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._consultas = _PacientesConsultasSqlite(connection)
        self._csv = _PacientesCsvSqlite()

    def create(self, paciente: Paciente) -> int:
        paciente.validar()
        cur = self._con.execute(
            """
            INSERT INTO pacientes (
                tipo_documento, documento,
                nombre, apellidos,
                telefono, email,
                fecha_nacimiento, direccion,
                activo,
                num_historia, alergias, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paciente.tipo_documento.value,
                paciente.documento,
                paciente.nombre,
                paciente.apellidos,
                paciente.telefono,
                paciente.email,
                format_iso_date(paciente.fecha_nacimiento),
                paciente.direccion,
                int(paciente.activo),
                None,
                paciente.alergias,
                paciente.observaciones,
            ),
        )
        paciente_id = int(cur.lastrowid)
        num_historia = self._format_num_historia(paciente_id)
        self._con.execute(
            "UPDATE pacientes SET num_historia = ? WHERE id = ?",
            (num_historia, paciente_id),
        )
        self._con.commit()
        return paciente_id

    def update(self, paciente: Paciente) -> None:
        if not paciente.id:
            raise ValidationError("No se puede actualizar un paciente sin id.")
        paciente.validar()
        self._con.execute(
            """
            UPDATE pacientes SET
                tipo_documento = ?,
                documento = ?,
                nombre = ?,
                apellidos = ?,
                telefono = ?,
                email = ?,
                fecha_nacimiento = ?,
                direccion = ?,
                activo = ?,
                alergias = ?,
                observaciones = ?
            WHERE id = ?
            """,
            (
                paciente.tipo_documento.value,
                paciente.documento,
                paciente.nombre,
                paciente.apellidos,
                paciente.telefono,
                paciente.email,
                format_iso_date(paciente.fecha_nacimiento),
                paciente.direccion,
                int(paciente.activo),
                paciente.alergias,
                paciente.observaciones,
                paciente.id,
            ),
        )
        self._con.commit()

    def delete(self, paciente_id: int) -> None:
        self._con.execute("UPDATE pacientes SET activo = 0 WHERE id = ?", (paciente_id,))
        self._con.commit()

    def get_by_id(self, paciente_id: int) -> Optional[Paciente]:
        return self._consultas.get_by_id(paciente_id)

    def get_id_by_documento(
        self,
        tipo_documento: TipoDocumento | str,
        documento: str,
    ) -> Optional[int]:
        return self._consultas.get_id_by_documento(tipo_documento, documento)

    def list_all(self, *, solo_activos: bool = True) -> List[Paciente]:
        return self._consultas.list_all(solo_activos=solo_activos)

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Paciente]:
        return self._consultas.search(
            texto=texto,
            tipo_documento=tipo_documento,
            documento=documento,
            activo=activo,
        )

    def export_csv(self, path: Path, pacientes: Iterable[Paciente]) -> None:
        self._csv.export_csv(path, pacientes)

    def import_csv(self, path: Path) -> int:
        pacientes = self._csv.import_csv(path)
        for paciente in pacientes:
            self.create(paciente)
        return len(pacientes)

    @staticmethod
    def _format_num_historia(paciente_id: int) -> str:
        return f"HIST-{paciente_id:04d}"
