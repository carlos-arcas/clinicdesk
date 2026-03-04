"""Entidades de dominio para stock de farmacia."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from clinicdesk.app.domain.enums import TipoMovimientoStock
from clinicdesk.app.domain.value_objects import (
    _ensure_non_negative,
    _ensure_positive_id,
    _require_non_empty,
    _strip_or_none,
)


@dataclass(slots=True)
class Medicamento:
    """Medicamento (tabla SQL: medicamentos)."""

    id: Optional[int] = None
    nombre_compuesto: str = ""
    nombre_comercial: str = ""
    cantidad_almacen: int = 0
    activo: bool = True

    def validar(self) -> None:
        self.nombre_compuesto = _require_non_empty(self.nombre_compuesto, "nombre_compuesto")
        self.nombre_comercial = _require_non_empty(self.nombre_comercial, "nombre_comercial")
        _ensure_non_negative(self.cantidad_almacen, "cantidad_almacen")

    def nombre_para_listado(self) -> str:
        return f"{self.nombre_comercial} ({self.nombre_compuesto})"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def cantidad_en_almacen(self) -> int:
        return self.cantidad_almacen

    @cantidad_en_almacen.setter
    def cantidad_en_almacen(self, value: int) -> None:
        self.cantidad_almacen = value


@dataclass(slots=True)
class Material:
    """Material (tabla SQL: materiales)."""

    id: Optional[int] = None
    nombre: str = ""
    fungible: bool = True
    cantidad_almacen: int = 0
    activo: bool = True

    def validar(self) -> None:
        self.nombre = _require_non_empty(self.nombre, "nombre")
        _ensure_non_negative(self.cantidad_almacen, "cantidad_almacen")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def cantidad_en_almacen(self) -> int:
        return self.cantidad_almacen

    @cantidad_en_almacen.setter
    def cantidad_en_almacen(self, value: int) -> None:
        self.cantidad_almacen = value


@dataclass(slots=True)
class MovimientoMedicamento:
    id: Optional[int] = None
    medicamento_id: int = 0
    fecha_hora: datetime = field(default_factory=datetime.now)
    tipo: TipoMovimientoStock = TipoMovimientoStock.ENTRADA
    cantidad: int = 0
    motivo: Optional[str] = None
    receta_id: Optional[int] = None
    dispensacion_id: Optional[int] = None
    personal_id: Optional[int] = None

    def validar(self) -> None:
        _ensure_positive_id(self.medicamento_id, "medicamento_id")
        _ensure_non_negative(self.cantidad, "cantidad")
        self.motivo = _strip_or_none(self.motivo)

    def delta_stock(self) -> int:
        if self.tipo == TipoMovimientoStock.ENTRADA:
            return self.cantidad
        if self.tipo == TipoMovimientoStock.SALIDA:
            return -self.cantidad
        return self.cantidad

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tipo"] = self.tipo.value
        data["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        return data


@dataclass(slots=True)
class MovimientoMaterial:
    id: Optional[int] = None
    material_id: int = 0
    fecha_hora: datetime = field(default_factory=datetime.now)
    tipo: TipoMovimientoStock = TipoMovimientoStock.ENTRADA
    cantidad: int = 0
    motivo: Optional[str] = None
    personal_id: Optional[int] = None

    def validar(self) -> None:
        _ensure_positive_id(self.material_id, "material_id")
        _ensure_non_negative(self.cantidad, "cantidad")
        self.motivo = _strip_or_none(self.motivo)

    def delta_stock(self) -> int:
        if self.tipo == TipoMovimientoStock.ENTRADA:
            return self.cantidad
        if self.tipo == TipoMovimientoStock.SALIDA:
            return -self.cantidad
        return self.cantidad

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tipo"] = self.tipo.value
        data["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        return data


__all__ = [
    "Medicamento",
    "Material",
    "MovimientoMedicamento",
    "MovimientoMaterial",
]
