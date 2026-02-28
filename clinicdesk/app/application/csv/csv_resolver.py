from __future__ import annotations

from typing import Dict, Optional


class CsvResolverMixin:
    def _resolve_person_id(self, table: str, row: Dict[str, str]) -> Optional[int]:
        rid = self._lookup_existing_id(table, self._to_int(row.get("id")))
        if rid is not None:
            return rid

        tipo_documento_raw = (row.get("tipo_documento") or "").strip()
        documento = (row.get("documento") or "").strip()
        if not tipo_documento_raw or not documento:
            return None

        tipo_documento = self._parse_tipo_documento(tipo_documento_raw).value
        query = f"SELECT id FROM {table} WHERE tipo_documento = ? AND documento = ? LIMIT 1"
        found = self._c.connection.execute(query, (tipo_documento, documento)).fetchone()
        return int(found["id"]) if found else None

    def _resolve_medico_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._lookup_existing_id("medicos", self._to_int(row.get("id")))
        if rid is not None:
            return rid

        num_colegiado = (row.get("num_colegiado") or "").strip()
        if num_colegiado:
            found = self._c.connection.execute(
                "SELECT id FROM medicos WHERE num_colegiado = ? LIMIT 1",
                (num_colegiado,),
            ).fetchone()
            if found:
                return int(found["id"])

        return self._resolve_person_id("medicos", row)

    def _resolve_medicamento_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._lookup_existing_id("medicamentos", self._to_int(row.get("id")))
        if rid is not None:
            return rid

        nc = (row.get("nombre_comercial") or "").strip()
        ncp = (row.get("nombre_compuesto") or "").strip()
        if not nc or not ncp:
            return None

        found = self._c.connection.execute(
            """
            SELECT id FROM medicamentos
            WHERE nombre_comercial = ? AND nombre_compuesto = ?
            LIMIT 1
            """,
            (nc, ncp),
        ).fetchone()
        return int(found["id"]) if found else None

    def _resolve_material_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._lookup_existing_id("materiales", self._to_int(row.get("id")))
        if rid is not None:
            return rid

        nombre = (row.get("nombre") or "").strip()
        if not nombre:
            return None

        found = self._c.connection.execute(
            "SELECT id FROM materiales WHERE nombre = ? LIMIT 1",
            (nombre,),
        ).fetchone()
        return int(found["id"]) if found else None

    def _resolve_sala_id(self, row: Dict[str, str]) -> Optional[int]:
        rid = self._lookup_existing_id("salas", self._to_int(row.get("id")))
        if rid is not None:
            return rid

        nombre = (row.get("nombre") or "").strip()
        if not nombre:
            return None

        found = self._c.connection.execute(
            "SELECT id FROM salas WHERE nombre = ? LIMIT 1",
            (nombre,),
        ).fetchone()
        return int(found["id"]) if found else None

    def _lookup_existing_id(self, table: str, rid: Optional[int]) -> Optional[int]:
        if not rid:
            return None
        exists = self._c.connection.execute(f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1", (rid,)).fetchone()
        return rid if exists else None
