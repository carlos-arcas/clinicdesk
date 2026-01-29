# application/usecases/csv/csv_service.py
"""
Servicio CSV de importación/exportación.

Diseño:
- Export: lee repos -> genera rows -> write_csv
- Import: read_csv -> por fila decide create/update (upsert)
- Errores por fila, sin abortar todo el proceso

Estrategia upsert:
- Si viene "id" y existe -> update
- Si no hay id:
  - Personas: usa (tipo_documento, documento) como clave natural
  - Médicos: prioriza num_colegiado si existe
  - Medicamentos: (nombre_comercial + nombre_compuesto)
  - Materiales: nombre
  - Salas: nombre
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from clinicdesk.app.container import AppContainer
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Paciente, Medico, Personal, Medicamento, Material, Sala

from clinicdesk.app.application.csv.csv_io import CsvRowError, read_csv, write_csv


# ---------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------


@dataclass(slots=True)
class CsvImportResult:
    created: int
    updated: int
    errors: List[CsvRowError]


# ---------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------


class CsvService:
    def __init__(self, container: AppContainer) -> None:
        self._c = container

    # ==============================================================
    # EXPORTS
    # ==============================================================

    def export_pacientes(self, path: str) -> None:
        headers = [
            "id", "tipo_documento", "documento", "nombre", "apellidos",
            "telefono", "email", "fecha_nacimiento", "direccion", "activo",
            "num_historia"
        ]
        pacientes = self._c.pacientes_repo.list_all(solo_activos=False)
        rows = [self._paciente_to_row(p) for p in pacientes]
        write_csv(path, headers=headers, rows=rows)

    def export_medicos(self, path: str) -> None:
        headers = [
            "id", "tipo_documento", "documento", "nombre", "apellidos",
            "telefono", "email", "fecha_nacimiento", "direccion", "activo",
            "num_colegiado", "especialidad"
        ]
        medicos = self._c.medicos_repo.list_all(solo_activos=False)
        rows = [self._medico_to_row(m) for m in medicos]
        write_csv(path, headers=headers, rows=rows)

    def export_personal(self, path: str) -> None:
        headers = [
            "id", "tipo_documento", "documento", "nombre", "apellidos",
            "telefono", "email", "fecha_nacimiento", "direccion", "activo",
            "puesto", "turno"
        ]
        personal = self._c.personal_repo.list_all(solo_activos=False)
        rows = [self._personal_to_row(p) for p in personal]
        write_csv(path, headers=headers, rows=rows)

    def export_medicamentos(self, path: str) -> None:
        headers = ["id", "nombre_compuesto", "nombre_comercial", "cantidad_en_almacen", "activo"]
        meds = self._c.medicamentos_repo.list_all(solo_activos=False)
        rows = [self._medicamento_to_row(m) for m in meds]
        write_csv(path, headers=headers, rows=rows)

    def export_materiales(self, path: str) -> None:
        headers = ["id", "nombre", "fungible", "cantidad_en_almacen", "activo"]
        mats = self._c.materiales_repo.list_all(solo_activos=False)
        rows = [self._material_to_row(m) for m in mats]
        write_csv(path, headers=headers, rows=rows)

    def export_salas(self, path: str) -> None:
        headers = ["id", "nombre", "tipo", "ubicacion", "activa"]
        salas = self._c.salas_repo.list_all(solo_activas=False)
        rows = [self._sala_to_row(s) for s in salas]
        write_csv(path, headers=headers, rows=rows)

    # ==============================================================
    # IMPORTS (UPSERT)
    # ==============================================================

    def import_pacientes(self, path: str) -> CsvImportResult:
        required = ["tipo_documento", "documento", "nombre", "apellidos"]
        data = read_csv(path, required_headers=required)

        created = 0
        updated = 0
        errors = list(data.errors)

        for i, row in enumerate(data.rows, start=2):
            try:
                paciente = self._row_to_paciente(row)
                existing_id = self._resolve_person_id("pacientes", row)

                if existing_id:
                    paciente.id = existing_id
                    self._c.pacientes_repo.update(paciente)
                    updated += 1
                else:
                    self._c.pacientes_repo.create(paciente)
                    created += 1
            except Exception as e:
                errors.append(CsvRowError(i, self._format_row_error(e), row))

        return CsvImportResult(created=created, updated=updated, errors=errors)

    def import_medicos(self, path: str) -> CsvImportResult:
        required = ["tipo_documento", "documento", "nombre", "apellidos"]
        data = read_csv(path, required_headers=required)

        created = 0
        updated = 0
        errors = list(data.errors)

        for i, row in enumerate(data.rows, start=2):
            try:
                medico = self._row_to_medico(row)
                existing_id = self._resolve_medico_id(row)

                if existing_id:
                    medico.id = existing_id
                    self._c.medicos_repo.update(medico)
                    updated += 1
                else:
                    self._c.medicos_repo.create(medico)
                    created += 1
            except Exception as e:
                errors.append(CsvRowError(i, self._format_row_error(e), row))

        return CsvImportResult(created=created, updated=updated, errors=errors)

    def import_personal(self, path: str) -> CsvImportResult:
        required = ["tipo_documento", "documento", "nombre", "apellidos"]
        data = read_csv(path, required_headers=required)

        created = 0
        updated = 0
        errors = list(data.errors)

        for i, row in enumerate(data.rows, start=2):
            try:
                personal = self._row_to_personal(row)
                existing_id = self._resolve_person_id("personal", row)

                if existing_id:
                    personal.id = existing_id
                    self._c.personal_repo.update(personal)
                    updated += 1
                else:
                    self._c.personal_repo.create(personal)
                    created += 1
            except Exception as e:
                errors.append(CsvRowError(i, self._format_row_error(e), row))

        return CsvImportResult(created=created, updated=updated, errors=errors)

    def import_medicamentos(self, path: str) -> CsvImportResult:
        required = ["nombre_compuesto", "nombre_comercial"]
        data = read_csv(path, required_headers=required)

        created = 0
        updated = 0
        errors = list(data.errors)

        for i, row in enumerate(data.rows, start=2):
            try:
                med = self._row_to_medicamento(row)
                existing_id = self._resolve_medicamento_id(row)

                if existing_id:
                    med.id = existing_id
                    self._c.medicamentos_repo.update(med)
                    updated += 1
                else:
                    self._c.medicamentos_repo.create(med)
                    created += 1
            except Exception as e:
                errors.append(CsvRowError(i, self._format_row_error(e), row))

        return CsvImportResult(created=created, updated=updated, errors=errors)

    def import_materiales(self, path: str) -> CsvImportResult:
        required = ["nombre", "fungible"]
        data = read_csv(path, required_headers=required)

        created = 0
        updated = 0
        errors = list(data.errors)

        for i, row in enumerate(data.rows, start=2):
            try:
                mat = self._row_to_material(row)
                existing_id = self._resolve_material_id(row)

                if existing_id:
                    mat.id = existing_id
                    self._c.materiales_repo.update(mat)
                    updated += 1
                else:
                    self._c.materiales_repo.create(mat)
                    created += 1
            except Exception as e:
                errors.append(CsvRowError(i, self._format_row_error(e), row))

        return CsvImportResult(created=created, updated=updated, errors=errors)

    def import_salas(self, path: str) -> CsvImportResult:
        required = ["nombre", "tipo"]
        data = read_csv(path, required_headers=required)

        created = 0
        updated = 0
        errors = list(data.errors)

        for i, row in enumerate(data.rows, start=2):
            try:
                sala = self._row_to_sala(row)
                existing_id = self._resolve_sala_id(row)

                if existing_id:
                    sala.id = existing_id
                    self._c.salas_repo.update(sala)
                    updated += 1
                else:
                    self._c.salas_repo.create(sala)
                    created += 1
            except Exception as e:
                errors.append(CsvRowError(i, self._format_row_error(e), row))

        return CsvImportResult(created=created, updated=updated, errors=errors)

    # ==============================================================
    # Resolución IDs (upsert)
    # ==============================================================

    def _resolve_person_id(self, table: str, row: Dict[str, str]) -> Optional[int]:
        """
        Para pacientes/medicos/personal:
        - Si viene id y existe -> usarlo
        - Si no, buscar por (tipo_documento, documento) (clave natural)
        """
        rid = self._to_int(row.get("id"))
        if rid:
            exists = self._c.connection.execute(f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1", (rid,)).fetchone()
            if exists:
                return rid

        tipo_documento_raw = (row.get("tipo_documento") or "").strip()
        documento = (row.get("documento") or "").strip()
        if not tipo_documento_raw or not documento:
            return None

        tipo_documento = self._parse_tipo_documento(tipo_documento_raw).value
        r = self._c.connection.execute(
            f"SELECT id FROM {table} WHERE tipo_documento = ? AND documento = ? LIMIT 1",
            (tipo_documento, documento),
        ).fetchone()
        return int(r["id"]) if r else None

    def _resolve_medico_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._to_int(row.get("id"))
        if rid:
            exists = self._c.connection.execute("SELECT 1 FROM medicos WHERE id = ? LIMIT 1", (rid,)).fetchone()
            if exists:
                return rid

        num_colegiado = (row.get("num_colegiado") or "").strip()
        if num_colegiado:
            r = self._c.connection.execute(
                "SELECT id FROM medicos WHERE num_colegiado = ? LIMIT 1",
                (num_colegiado,),
            ).fetchone()
            if r:
                return int(r["id"])

        return self._resolve_person_id("medicos", row)

    def _resolve_medicamento_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._to_int(row.get("id"))
        if rid:
            exists = self._c.connection.execute("SELECT 1 FROM medicamentos WHERE id = ? LIMIT 1", (rid,)).fetchone()
            if exists:
                return rid

        nc = (row.get("nombre_comercial") or "").strip()
        ncp = (row.get("nombre_compuesto") or "").strip()
        if not nc or not ncp:
            return None

        r = self._c.connection.execute(
            """
            SELECT id FROM medicamentos
            WHERE nombre_comercial = ? AND nombre_compuesto = ?
            LIMIT 1
            """,
            (nc, ncp),
        ).fetchone()
        return int(r["id"]) if r else None

    def _resolve_material_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._to_int(row.get("id"))
        if rid:
            exists = self._c.connection.execute("SELECT 1 FROM materiales WHERE id = ? LIMIT 1", (rid,)).fetchone()
            if exists:
                return rid

        nombre = (row.get("nombre") or "").strip()
        if not nombre:
            return None

        r = self._c.connection.execute(
            "SELECT id FROM materiales WHERE nombre = ? LIMIT 1",
            (nombre,),
        ).fetchone()
        return int(r["id"]) if r else None

    def _resolve_sala_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._to_int(row.get("id"))
        if rid:
            exists = self._c.connection.execute("SELECT 1 FROM salas WHERE id = ? LIMIT 1", (rid,)).fetchone()
            if exists:
                return rid

        nombre = (row.get("nombre") or "").strip()
        if not nombre:
            return None

        r = self._c.connection.execute(
            "SELECT id FROM salas WHERE nombre = ? LIMIT 1",
            (nombre,),
        ).fetchone()
        return int(r["id"]) if r else None

    # ==============================================================
    # Row -> Modelo
    # ==============================================================

    def _row_to_paciente(self, row: Dict[str, str]) -> Paciente:
        return Paciente(
            id=None,
            tipo_documento=self._parse_tipo_documento(row.get("tipo_documento")),
            documento=(row.get("documento") or "").strip(),
            nombre=(row.get("nombre") or "").strip(),
            apellidos=(row.get("apellidos") or "").strip(),
            telefono=self._none_if_empty(row.get("telefono")),
            email=self._none_if_empty(row.get("email")),
            fecha_nacimiento=self._parse_date_optional(row.get("fecha_nacimiento")),
            direccion=self._none_if_empty(row.get("direccion")),
            activo=self._parse_bool_default(row.get("activo"), default=True),
            num_historia=self._none_if_empty(row.get("num_historia")),
        )

    def _row_to_medico(self, row: Dict[str, str]) -> Medico:
        return Medico(
            id=None,
            tipo_documento=self._parse_tipo_documento(row.get("tipo_documento")),
            documento=(row.get("documento") or "").strip(),
            nombre=(row.get("nombre") or "").strip(),
            apellidos=(row.get("apellidos") or "").strip(),
            telefono=self._none_if_empty(row.get("telefono")),
            email=self._none_if_empty(row.get("email")),
            fecha_nacimiento=self._parse_date_optional(row.get("fecha_nacimiento")),
            direccion=self._none_if_empty(row.get("direccion")),
            activo=self._parse_bool_default(row.get("activo"), default=True),
            num_colegiado=self._none_if_empty(row.get("num_colegiado")),
            especialidad=self._none_if_empty(row.get("especialidad")),
        )

    def _row_to_personal(self, row: Dict[str, str]) -> Personal:
        return Personal(
            id=None,
            tipo_documento=self._parse_tipo_documento(row.get("tipo_documento")),
            documento=(row.get("documento") or "").strip(),
            nombre=(row.get("nombre") or "").strip(),
            apellidos=(row.get("apellidos") or "").strip(),
            telefono=self._none_if_empty(row.get("telefono")),
            email=self._none_if_empty(row.get("email")),
            fecha_nacimiento=self._parse_date_optional(row.get("fecha_nacimiento")),
            direccion=self._none_if_empty(row.get("direccion")),
            activo=self._parse_bool_default(row.get("activo"), default=True),
            puesto=self._none_if_empty(row.get("puesto")),
            turno=self._none_if_empty(row.get("turno")),
        )

    def _row_to_medicamento(self, row: Dict[str, str]) -> Medicamento:
        return Medicamento(
            id=None,
            nombre_compuesto=(row.get("nombre_compuesto") or "").strip(),
            nombre_comercial=(row.get("nombre_comercial") or "").strip(),
            cantidad_en_almacen=self._to_int(row.get("cantidad_en_almacen")) or 0,
            activo=self._parse_bool_default(row.get("activo"), default=True),
        )

    def _row_to_material(self, row: Dict[str, str]) -> Material:
        return Material(
            id=None,
            nombre=(row.get("nombre") or "").strip(),
            fungible=self._parse_bool_default(row.get("fungible"), default=True),
            cantidad_en_almacen=self._to_int(row.get("cantidad_en_almacen")) or 0,
            activo=self._parse_bool_default(row.get("activo"), default=True),
        )

    def _row_to_sala(self, row: Dict[str, str]) -> Sala:
        return Sala(
            id=None,
            nombre=(row.get("nombre") or "").strip(),
            tipo=self._parse_tipo_sala(row.get("tipo")),
            ubicacion=self._none_if_empty(row.get("ubicacion")),
            activa=self._parse_bool_default(row.get("activa"), default=True),
        )

    # ==============================================================
    # Modelo -> Row (export)
    # ==============================================================

    def _paciente_to_row(self, p: Paciente) -> Dict[str, Any]:
        return {
            "id": p.id,
            "tipo_documento": p.tipo_documento.value,
            "documento": p.documento,
            "nombre": p.nombre,
            "apellidos": p.apellidos,
            "telefono": p.telefono or "",
            "email": p.email or "",
            "fecha_nacimiento": p.fecha_nacimiento.isoformat() if p.fecha_nacimiento else "",
            "direccion": p.direccion or "",
            "activo": 1 if p.activo else 0,
            "num_historia": getattr(p, "num_historia", "") or "",
        }

    def _medico_to_row(self, m: Medico) -> Dict[str, Any]:
        return {
            "id": m.id,
            "tipo_documento": m.tipo_documento.value,
            "documento": m.documento,
            "nombre": m.nombre,
            "apellidos": m.apellidos,
            "telefono": m.telefono or "",
            "email": m.email or "",
            "fecha_nacimiento": m.fecha_nacimiento.isoformat() if m.fecha_nacimiento else "",
            "direccion": m.direccion or "",
            "activo": 1 if m.activo else 0,
            "num_colegiado": getattr(m, "num_colegiado", "") or "",
            "especialidad": getattr(m, "especialidad", "") or "",
        }

    def _personal_to_row(self, p: Personal) -> Dict[str, Any]:
        return {
            "id": p.id,
            "tipo_documento": p.tipo_documento.value,
            "documento": p.documento,
            "nombre": p.nombre,
            "apellidos": p.apellidos,
            "telefono": p.telefono or "",
            "email": p.email or "",
            "fecha_nacimiento": p.fecha_nacimiento.isoformat() if p.fecha_nacimiento else "",
            "direccion": p.direccion or "",
            "activo": 1 if p.activo else 0,
            "puesto": getattr(p, "puesto", "") or "",
            "turno": getattr(p, "turno", "") or "",
        }

    def _medicamento_to_row(self, m: Medicamento) -> Dict[str, Any]:
        return {
            "id": m.id,
            "nombre_compuesto": m.nombre_compuesto,
            "nombre_comercial": m.nombre_comercial,
            "cantidad_en_almacen": m.cantidad_en_almacen,
            "activo": 1 if m.activo else 0,
        }

    def _material_to_row(self, m: Material) -> Dict[str, Any]:
        return {
            "id": m.id,
            "nombre": m.nombre,
            "fungible": 1 if m.fungible else 0,
            "cantidad_en_almacen": m.cantidad_en_almacen,
            "activo": 1 if m.activo else 0,
        }

    def _sala_to_row(self, s: Sala) -> Dict[str, Any]:
        return {
            "id": s.id,
            "nombre": s.nombre,
            "tipo": s.tipo.value,
            "ubicacion": s.ubicacion or "",
            "activa": 1 if s.activa else 0,
        }

    # ==============================================================
    # Parsers / utils
    # ==============================================================

    def _parse_tipo_documento(self, v: Optional[str]) -> TipoDocumento:
        val = (v or "").strip()
        if not val:
            raise ValidationError("tipo_documento obligatorio.")

        normalized = self._normalize_enum_token(val)
        mapping = {self._normalize_enum_token(t.value): t for t in TipoDocumento}
        tipo = mapping.get(normalized)
        if tipo:
            return tipo

        opciones = ", ".join(t.value for t in TipoDocumento)
        raise ValidationError(f"tipo_documento inválido: {val}. Opciones válidas: {opciones}.")

    def _parse_tipo_sala(self, v: Optional[str]) -> TipoSala:
        val = (v or "").strip()
        if not val:
            raise ValidationError("tipo (sala) obligatorio.")

        normalized = self._normalize_enum_token(val)
        mapping = {self._normalize_enum_token(t.value): t for t in TipoSala}
        tipo = mapping.get(normalized)
        if tipo:
            return tipo

        opciones = ", ".join(t.value for t in TipoSala)
        raise ValidationError(f"tipo de sala inválido: {val}. Opciones válidas: {opciones}.")

    def _parse_date_optional(self, v: Optional[str]) -> Optional[date]:
        val = (v or "").strip()
        if not val:
            return None
        try:
            return date.fromisoformat(val)
        except ValueError as e:
            raise ValidationError("fecha_nacimiento: formato inválido (AAAA-MM-DD)") from e

    def _parse_bool_default(self, v: Optional[str], *, default: bool) -> bool:
        val = (v or "").strip().lower()
        if val == "":
            return default
        if val in ("1", "true", "t", "si", "sí", "yes", "y"):
            return True
        if val in ("0", "false", "f", "no", "n"):
            return False
        raise ValidationError(f"Valor booleano inválido: {v}")

    def _to_int(self, v: Optional[str]) -> Optional[int]:
        val = (v or "").strip()
        if not val:
            return None
        try:
            return int(val)
        except ValueError as e:
            raise ValidationError(f"Entero inválido: {v}") from e

    def _none_if_empty(self, v: Optional[str]) -> Optional[str]:
        val = (v or "").strip()
        return val if val else None

    def _normalize_enum_token(self, value: str) -> str:
        return value.strip().upper().replace(".", "").replace(" ", "")

    def _format_row_error(self, exc: Exception) -> str:
        if isinstance(exc, ValidationError):
            return str(exc)

        if isinstance(exc, ValueError) and "isoformat" in str(exc).lower():
            return "fecha_nacimiento: formato inválido (AAAA-MM-DD)"

        if isinstance(exc, sqlite3.IntegrityError):
            message = str(exc).lower()
            if "num_colegiado" in message:
                return "num_colegiado duplicado"
            if "tipo_documento" in message and "documento" in message:
                return "registro duplicado: (tipo_documento, documento) ya existe"
            return "registro duplicado"

        return "Error inesperado al importar la fila."
