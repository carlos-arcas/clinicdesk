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
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class PacientesRepository:
    """
    Repositorio de acceso a datos para pacientes.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, paciente: Paciente) -> int:
        """
        Inserta un nuevo paciente y devuelve su id.
        """
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
                paciente.num_historia,
                paciente.alergias,
                paciente.observaciones,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, paciente: Paciente) -> None:
        """
        Actualiza un paciente existente.
        """
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
                num_historia = ?,
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
                paciente.num_historia,
                paciente.alergias,
                paciente.observaciones,
                paciente.id,
            ),
        )
        self._con.commit()

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

        rows = self._con.execute(sql, params).fetchall()
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
        clauses: list[str] = []
        params: list = []

        if texto:
            clauses.append("(nombre LIKE ? OR apellidos LIKE ? OR documento LIKE ?)")
            like = f"%{texto}%"
            params.extend([like, like, like])

        if tipo_documento:
            clauses.append("tipo_documento = ?")
            params.append(tipo_documento.value)

        if documento:
            clauses.append("documento = ?")
            params.append(documento)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT * FROM pacientes"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY apellidos, nombre"

        rows = self._con.execute(sql, params).fetchall()
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
                    num_historia=row.get("num_historia") or None,
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
