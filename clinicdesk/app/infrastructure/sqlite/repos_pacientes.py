from __future__ import annotations

import csv
import logging
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date
from clinicdesk.app.infrastructure.sqlite.paciente_field_crypto import (
    build_protected_fields,
    documento_hash_for_query,
    email_hash_for_query,
    resolve_field,
    telefono_hash_for_query,
)

logger = logging.getLogger(__name__)


def _legacy_documento_value(value: str, doc_hash: Optional[str]) -> str:
    return f"enc:{doc_hash[:16]}" if doc_hash else value


def _legacy_value(legacy: Optional[str], encrypted: Optional[str]) -> Optional[str]:
    return None if encrypted else legacy


def _row_to_model(row: sqlite3.Row) -> Paciente:
    return Paciente(
        id=row["id"],
        tipo_documento=TipoDocumento(row["tipo_documento"]),
        documento=resolve_field(legacy=row["documento"], encrypted=row["documento_enc"]),
        nombre=row["nombre"],
        apellidos=row["apellidos"],
        telefono=resolve_field(legacy=row["telefono"], encrypted=row["telefono_enc"]),
        email=resolve_field(legacy=row["email"], encrypted=row["email_enc"]),
        fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
        direccion=resolve_field(legacy=row["direccion"], encrypted=row["direccion_enc"]),
        activo=bool(row["activo"]),
        num_historia=row["num_historia"],
        alergias=row["alergias"],
        observaciones=row["observaciones"],
    )


def _build_text_clause(texto: Optional[str], params: list[object]) -> Optional[str]:
    if not texto:
        return None
    like = like_value(texto)
    clauses = ["nombre LIKE ? COLLATE NOCASE", "apellidos LIKE ? COLLATE NOCASE", "documento LIKE ? COLLATE NOCASE"]
    params.extend([like, like, like])
    for hash_value, sql in (
        (documento_hash_for_query(texto), "documento_hash = ?"),
        (telefono_hash_for_query(texto), "telefono_hash = ?"),
        (email_hash_for_query(texto), "email_hash = ?"),
    ):
        if hash_value:
            clauses.append(sql)
            params.append(hash_value)
    return "(" + " OR ".join(clauses) + ")"


def _append_documento_clause(documento: Optional[str], clauses: list[str], params: list[object]) -> None:
    if not documento:
        return
    doc_hash = documento_hash_for_query(documento)
    if doc_hash:
        clauses.append("(documento_hash = ? OR documento LIKE ? COLLATE NOCASE)")
        params.extend([doc_hash, like_value(documento)])
        return
    clauses.append("documento LIKE ? COLLATE NOCASE")
    params.append(like_value(documento))


def _search_sql(clauses: list[str]) -> str:
    sql = "SELECT * FROM pacientes"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    return sql + " ORDER BY apellidos, nombre"


def _csv_row_to_paciente(row: dict[str, str]) -> Paciente:
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


class PacientesRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def create(self, paciente: Paciente) -> int:
        paciente.validar()
        protected = build_protected_fields(
            documento=paciente.documento,
            email=paciente.email,
            telefono=paciente.telefono,
            direccion=paciente.direccion,
        )
        cur = self._con.execute(
            """
            INSERT INTO pacientes (
                tipo_documento, documento, nombre, apellidos,
                telefono, email, fecha_nacimiento, direccion,
                documento_enc, email_enc, telefono_enc, direccion_enc,
                documento_hash, email_hash, telefono_hash,
                activo, num_historia, alergias, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paciente.tipo_documento.value,
                _legacy_documento_value(paciente.documento, protected.documento_hash),
                paciente.nombre,
                paciente.apellidos,
                _legacy_value(paciente.telefono, protected.telefono_enc),
                _legacy_value(paciente.email, protected.email_enc),
                format_iso_date(paciente.fecha_nacimiento),
                _legacy_value(paciente.direccion, protected.direccion_enc),
                protected.documento_enc,
                protected.email_enc,
                protected.telefono_enc,
                protected.direccion_enc,
                protected.documento_hash,
                protected.email_hash,
                protected.telefono_hash,
                int(paciente.activo),
                None,
                paciente.alergias,
                paciente.observaciones,
            ),
        )
        paciente_id = int(cur.lastrowid)
        self._con.execute("UPDATE pacientes SET num_historia = ? WHERE id = ?", (self._format_num_historia(paciente_id), paciente_id))
        self._con.commit()
        return paciente_id

    def update(self, paciente: Paciente) -> None:
        if not paciente.id:
            raise ValidationError("No se puede actualizar un paciente sin id.")
        paciente.validar()
        protected = build_protected_fields(
            documento=paciente.documento,
            email=paciente.email,
            telefono=paciente.telefono,
            direccion=paciente.direccion,
        )
        self._con.execute(
            """
            UPDATE pacientes SET
                tipo_documento = ?, documento = ?, nombre = ?, apellidos = ?,
                telefono = ?, email = ?, fecha_nacimiento = ?, direccion = ?,
                documento_enc = ?, email_enc = ?, telefono_enc = ?, direccion_enc = ?,
                documento_hash = ?, email_hash = ?, telefono_hash = ?,
                activo = ?, alergias = ?, observaciones = ?
            WHERE id = ?
            """,
            (
                paciente.tipo_documento.value,
                _legacy_documento_value(paciente.documento, protected.documento_hash),
                paciente.nombre,
                paciente.apellidos,
                _legacy_value(paciente.telefono, protected.telefono_enc),
                _legacy_value(paciente.email, protected.email_enc),
                format_iso_date(paciente.fecha_nacimiento),
                _legacy_value(paciente.direccion, protected.direccion_enc),
                protected.documento_enc,
                protected.email_enc,
                protected.telefono_enc,
                protected.direccion_enc,
                protected.documento_hash,
                protected.email_hash,
                protected.telefono_hash,
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
        row = self._con.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,)).fetchone()
        return _row_to_model(row) if row else None

    def get_id_by_documento(self, tipo_documento: TipoDocumento | str, documento: str) -> Optional[int]:
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        doc_hash = documento_hash_for_query(documento)
        if doc_hash:
            row = self._con.execute("SELECT id FROM pacientes WHERE tipo_documento = ? AND documento_hash = ?", (tipo, doc_hash)).fetchone()
            if row:
                return int(row["id"])
        row = self._con.execute("SELECT id FROM pacientes WHERE tipo_documento = ? AND documento = ?", (tipo, documento)).fetchone()
        return int(row["id"]) if row else None

    def list_all(self, *, solo_activos: bool = True) -> list[Paciente]:
        sql = "SELECT * FROM pacientes" + (" WHERE activo = 1" if solo_activos else "") + " ORDER BY apellidos, nombre"
        try:
            rows = self._con.execute(sql).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesRepository.list_all: %s", exc)
            return []
        return [_row_to_model(r) for r in rows]

    def search(self, *, texto: Optional[str] = None, tipo_documento: Optional[TipoDocumento] = None, documento: Optional[str] = None, activo: Optional[bool] = True) -> list[Paciente]:
        clauses: list[str] = []
        params: list[object] = []
        text_clause = _build_text_clause(normalize_search_text(texto), params)
        if text_clause:
            clauses.append(text_clause)
        tipo_documento_value = normalize_search_text(tipo_documento.value if tipo_documento else None)
        if tipo_documento_value:
            clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo_documento_value))
        _append_documento_clause(normalize_search_text(documento), clauses, params)
        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))
        try:
            rows = self._con.execute(_search_sql(clauses), params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesRepository.search: %s", exc)
            return []
        return [_row_to_model(r) for r in rows]

    def export_csv(self, path: Path, pacientes: Iterable[Paciente]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["tipo_documento", "documento", "nombre", "apellidos", "telefono", "email", "fecha_nacimiento", "direccion", "activo", "num_historia", "alergias", "observaciones"])
            writer.writeheader()
            for paciente in pacientes:
                payload = paciente.to_dict()
                payload.pop("id", None)
                writer.writerow(payload)

    def import_csv(self, path: Path) -> int:
        count = 0
        with path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                self.create(_csv_row_to_paciente(row))
                count += 1
        return count

    @staticmethod
    def _format_num_historia(paciente_id: int) -> str:
        return f"HIST-{paciente_id:04d}"
