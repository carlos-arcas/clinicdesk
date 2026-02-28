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

from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class PacientesRepository:
    """
    Repositorio de acceso a datos para pacientes.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._pii_cipher = get_connection_pii_cipher(connection)
        self._field_protection = PacientesFieldProtection(connection)

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, paciente: Paciente) -> int:
        """
        Inserta un nuevo paciente y devuelve su id.
        """
        paciente.validar()
        if self._field_protection.enabled:
            paciente_id = self._create_with_field_protection(paciente)
        else:
            paciente_id = self._create_legacy(paciente)
        num_historia = self._format_num_historia(paciente_id)
        self._con.execute(
            "UPDATE pacientes SET num_historia = ? WHERE id = ?",
            (num_historia, paciente_id),
        )
        self._con.commit()
        return paciente_id

    def update(self, paciente: Paciente) -> None:
        """
        Actualiza un paciente existente.
        """
        if not paciente.id:
            raise ValidationError("No se puede actualizar un paciente sin id.")

        paciente.validar()
        if self._field_protection.enabled:
            self._update_with_field_protection(paciente)
        else:
            self._update_legacy(paciente)
        self._con.commit()

    def _create_legacy(self, paciente: Paciente) -> int:
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
                self._encrypt(paciente.telefono),
                self._encrypt(paciente.email),
                format_iso_date(paciente.fecha_nacimiento),
                self._encrypt(paciente.direccion),
                int(paciente.activo),
                None,
                self._encrypt(paciente.alergias),
                self._encrypt(paciente.observaciones),
            ),
        )
        return int(cur.lastrowid)

    def _create_with_field_protection(self, paciente: Paciente) -> int:
        documento = self._field_protection.encode("documento", paciente.documento)
        telefono = self._field_protection.encode("telefono", paciente.telefono)
        email = self._field_protection.encode("email", paciente.email)
        direccion = self._field_protection.encode("direccion", paciente.direccion)
        cur = self._con.execute(
            """
            INSERT INTO pacientes (
                tipo_documento, documento, documento_enc, documento_hash,
                nombre, apellidos,
                telefono, telefono_enc, telefono_hash,
                email, email_enc, email_hash,
                fecha_nacimiento,
                direccion, direccion_enc, direccion_hash,
                activo,
                num_historia, alergias, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paciente.tipo_documento.value,
                documento.legacy,
                documento.encrypted,
                documento.lookup_hash,
                paciente.nombre,
                paciente.apellidos,
                self._encrypt(telefono.legacy),
                telefono.encrypted,
                telefono.lookup_hash,
                self._encrypt(email.legacy),
                email.encrypted,
                email.lookup_hash,
                format_iso_date(paciente.fecha_nacimiento),
                self._encrypt(direccion.legacy),
                direccion.encrypted,
                direccion.lookup_hash,
                int(paciente.activo),
                None,
                self._encrypt(paciente.alergias),
                self._encrypt(paciente.observaciones),
            ),
        )
        return int(cur.lastrowid)

    def _update_legacy(self, paciente: Paciente) -> None:
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
                self._encrypt(paciente.telefono),
                self._encrypt(paciente.email),
                format_iso_date(paciente.fecha_nacimiento),
                self._encrypt(paciente.direccion),
                int(paciente.activo),
                self._encrypt(paciente.alergias),
                self._encrypt(paciente.observaciones),
                paciente.id,
            ),
        )

    def _update_with_field_protection(self, paciente: Paciente) -> None:
        documento = self._field_protection.encode("documento", paciente.documento)
        telefono = self._field_protection.encode("telefono", paciente.telefono)
        email = self._field_protection.encode("email", paciente.email)
        direccion = self._field_protection.encode("direccion", paciente.direccion)
        self._con.execute(
            """
            UPDATE pacientes SET
                tipo_documento = ?,
                documento = ?,
                documento_enc = ?,
                documento_hash = ?,
                nombre = ?,
                apellidos = ?,
                telefono = ?,
                telefono_enc = ?,
                telefono_hash = ?,
                email = ?,
                email_enc = ?,
                email_hash = ?,
                fecha_nacimiento = ?,
                direccion = ?,
                direccion_enc = ?,
                direccion_hash = ?,
                activo = ?,
                alergias = ?,
                observaciones = ?
            WHERE id = ?
            """,
            (
                paciente.tipo_documento.value,
                documento.legacy,
                documento.encrypted,
                documento.lookup_hash,
                paciente.nombre,
                paciente.apellidos,
                self._encrypt(telefono.legacy),
                telefono.encrypted,
                telefono.lookup_hash,
                self._encrypt(email.legacy),
                email.encrypted,
                email.lookup_hash,
                format_iso_date(paciente.fecha_nacimiento),
                self._encrypt(direccion.legacy),
                direccion.encrypted,
                direccion.lookup_hash,
                int(paciente.activo),
                self._encrypt(paciente.alergias),
                self._encrypt(paciente.observaciones),
                paciente.id,
            ),
        )

    def delete(self, paciente_id: int) -> None:
        """
        Borrado lógico: marca el paciente como inactivo.
        """
        self._con.execute(
            "UPDATE pacientes SET activo = 0 WHERE id = ?",
            (paciente_id,),
        )
        self._con.commit()

    def get_by_id(self, paciente_id: int) -> Optional[Paciente]:
        """
        Obtiene un paciente por id.
        """
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
        """
        Obtiene el id del paciente a partir del tipo + documento.
        """
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        if self._field_protection.enabled:
            documento_hash = self._field_protection.hash_for_lookup("documento", documento)
            row = self._con.execute(
                "SELECT id FROM pacientes WHERE tipo_documento = ? AND documento_hash = ?",
                (tipo, documento_hash),
            ).fetchone()
        else:
            row = self._con.execute(
                "SELECT id FROM pacientes WHERE tipo_documento = ? AND documento = ?",
                (tipo, documento),
            ).fetchone()
        return int(row["id"]) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activos: bool = True) -> List[Paciente]:
        """
        Lista todos los pacientes.
        """
        sql = "SELECT * FROM pacientes"
        params: list = []

        if solo_activos:
            sql += " WHERE activo = 1"

        sql += " ORDER BY apellidos, nombre"

        try:
            rows = self._con.execute(sql, params).fetchall()
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
        """
        Búsqueda flexible de pacientes.

        Parámetros:
        - texto: busca en nombre, apellidos y documento
        - tipo_documento: filtra por tipo
        - documento: documento exacto
        - activo: True / False / None (None = todos)
        """
        texto = normalize_search_text(texto)
        documento = normalize_search_text(documento)
        tipo_documento_value = normalize_search_text(
            tipo_documento.value if tipo_documento else None
        )

        clauses: list[str] = []
        params: list = []

        if texto:
            like = like_value(texto)
            if self._field_protection.enabled:
                clauses.append("(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE)")
                params.extend([like, like])
            else:
                clauses.append(
                    "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
                    "OR documento LIKE ? COLLATE NOCASE)"
                )
                params.extend([like, like, like])

        if tipo_documento_value:
            clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo_documento_value))

        if documento:
            if self._field_protection.enabled:
                clauses.append("documento_hash = ?")
                params.append(self._field_protection.hash_for_lookup("documento", documento))
            else:
                clauses.append("documento LIKE ? COLLATE NOCASE")
                params.append(like_value(documento))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

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

    # --------------------------------------------------------------
    # CSV
    # --------------------------------------------------------------

    def export_csv(self, path: Path, pacientes: Iterable[Paciente]) -> None:
        """
        Exporta pacientes a CSV.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
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
                ],
            )
            writer.writeheader()

            for p in pacientes:
                d = p.to_dict()
                d.pop("id", None)
                writer.writerow(d)

    def import_csv(self, path: Path) -> int:
        """
        Importa pacientes desde CSV.
        Inserta nuevos registros; no hace update automático.

        Devuelve:
        - número de pacientes importados
        """
        count = 0

        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                paciente = Paciente(
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

                self.create(paciente)
                count += 1

        return count

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Paciente:
        """
        Convierte una fila SQLite en un modelo Paciente.
        """
        return Paciente(
            id=row["id"],
            tipo_documento=TipoDocumento(row["tipo_documento"]),
            documento=self._field_protection.decode(
                "documento",
                legacy=row["documento"],
                encrypted=self._row_value(row, "documento_enc"),
            )
            or "",
            nombre=row["nombre"],
            apellidos=row["apellidos"],
            telefono=self._field_protection.decode(
                "telefono",
                legacy=self._decrypt(row["telefono"]),
                encrypted=self._row_value(row, "telefono_enc"),
            ),
            email=self._field_protection.decode(
                "email",
                legacy=self._decrypt(row["email"]),
                encrypted=self._row_value(row, "email_enc"),
            ),
            fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
            direccion=self._field_protection.decode(
                "direccion",
                legacy=self._decrypt(row["direccion"]),
                encrypted=self._row_value(row, "direccion_enc"),
            ),
            activo=bool(row["activo"]),
            num_historia=row["num_historia"],
            alergias=self._decrypt(row["alergias"]),
            observaciones=self._decrypt(row["observaciones"]),
        )

    @staticmethod
    def _row_value(row: sqlite3.Row, column: str) -> str | None:
        return row[column] if column in row.keys() else None

    @staticmethod
    def _format_num_historia(paciente_id: int) -> str:
        return f"HIST-{paciente_id:04d}"

    def _encrypt(self, value: str | None) -> str | None:
        if self._pii_cipher is None:
            return value
        return self._pii_cipher.encrypt_optional(value)

    def _decrypt(self, value: str | None) -> str | None:
        if self._pii_cipher is None:
            return value
        return self._pii_cipher.decrypt_optional(value)
