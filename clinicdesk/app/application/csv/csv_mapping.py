from __future__ import annotations

from typing import Any, Dict

from clinicdesk.app.domain.modelos import Material, Medicamento, Medico, Paciente, Personal, Sala


class CsvMappingMixin:
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
            num_historia=None,
            alergias=self._none_if_empty(row.get("alergias")),
            observaciones=self._none_if_empty(row.get("observaciones")),
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
            "alergias": getattr(p, "alergias", "") or "",
            "observaciones": getattr(p, "observaciones", "") or "",
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
