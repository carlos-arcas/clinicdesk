# application/usecases/ajustar_stock_material.py
"""
Caso de uso: Ajustar stock de material (ENTRADA / SALIDA / AJUSTE).

Objetivo:
- Operación única y auditable sobre stock de materiales
- Actualiza stock actual (tabla materiales)
- Inserta movimiento (movimientos_materiales)

Reglas:
- Duro (NO override):
  - Material inexistente/inactivo
  - cantidad inválida (0)
  - SALIDA no puede dejar stock negativo

- Warnings (requieren guardado consciente):
  - AJUSTE grande (posible error)
  - ENTRADA grande
  - SALIDA grande

Guardado consciente:
- Si hay warnings, no guarda salvo override=True
- nota_override obligatoria
- confirmado_por_personal_id obligatorio

Notas:
- cantidad siempre es magnitud positiva
- el tipo indica la dirección del movimiento
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from clinicdesk.app.container import AppContainer
from clinicdesk.app.domain.exceptions import ValidationError


# ---------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------


@dataclass(slots=True)
class WarningItem:
    codigo: str
    mensaje: str
    severidad: str  # "BAJA" | "MEDIA" | "ALTA"


class PendingWarningsError(ValidationError):
    def __init__(self, warnings: List[WarningItem]) -> None:
        super().__init__("La operación requiere confirmación (override) por incidencias/warnings.")
        self.warnings = warnings


@dataclass(slots=True)
class AjustarStockMaterialRequest:
    material_id: int
    tipo: str                 # "ENTRADA" | "SALIDA" | "AJUSTE"
    cantidad: int             # magnitud (>0)
    personal_id: int

    motivo: Optional[str] = None
    referencia: Optional[str] = None
    fecha_hora: Optional[str] = None

    override: bool = False
    nota_override: Optional[str] = None
    confirmado_por_personal_id: Optional[int] = None


@dataclass(slots=True)
class AjustarStockMaterialResult:
    movimiento_id: int
    stock_anterior: int
    stock_nuevo: int
    warnings: List[WarningItem]
    incidencia_id: Optional[int]


# ---------------------------------------------------------------------
# Use case
# ---------------------------------------------------------------------


class AjustarStockMaterialUseCase:
    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def execute(self, req: AjustarStockMaterialRequest) -> AjustarStockMaterialResult:
        self._validate_request(req)
        fecha_hora, stock_anterior = self._load_state(req)
        stock_nuevo, warnings, mov_tipo, mov_cantidad = self._compute_changes(req, stock_anterior)
        incidencia_id, movimiento_id = self._persist(
            req=req,
            fecha_hora=fecha_hora,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            warnings=warnings,
            mov_tipo=mov_tipo,
            mov_cantidad=mov_cantidad,
        )
        return self._build_response(
            movimiento_id=movimiento_id,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            warnings=warnings,
            incidencia_id=incidencia_id,
        )

    def _validate_request(self, req: AjustarStockMaterialRequest) -> None:
        if req.material_id <= 0:
            raise ValidationError("material_id inválido.")
        if req.personal_id <= 0:
            raise ValidationError("personal_id inválido.")
        if req.cantidad <= 0:
            raise ValidationError("cantidad debe ser mayor que 0.")
        if req.tipo not in ("ENTRADA", "SALIDA", "AJUSTE"):
            raise ValidationError("tipo debe ser ENTRADA, SALIDA o AJUSTE.")

    def _load_state(self, req: AjustarStockMaterialRequest) -> Tuple[str, int]:
        fecha_hora = req.fecha_hora or self._now_iso()
        material = self._c.materiales_repo.get_by_id(req.material_id)
        if not material or not material.activo:
            raise ValidationError("El material no existe o está inactivo.")
        return fecha_hora, int(material.cantidad_en_almacen)

    def _compute_changes(self, req: AjustarStockMaterialRequest, stock_anterior: int) -> Tuple[int, List[WarningItem], str, int]:
        stock_nuevo = self._next_stock(req.tipo, stock_anterior, req.cantidad)
        warnings = self._build_warnings(req, stock_anterior, stock_nuevo)
        self._validate_override(req, warnings)
        mov_tipo, mov_cantidad = self._resolve_movement(req, stock_anterior, stock_nuevo)
        return stock_nuevo, warnings, mov_tipo, mov_cantidad

    def _persist(
        self,
        *,
        req: AjustarStockMaterialRequest,
        fecha_hora: str,
        stock_anterior: int,
        stock_nuevo: int,
        warnings: List[WarningItem],
        mov_tipo: str,
        mov_cantidad: int,
    ) -> Tuple[Optional[int], int]:
        from clinicdesk.app.infrastructure.sqlite.repos_movimientos_materiales import MovimientoMaterial

        mov = MovimientoMaterial(
            material_id=req.material_id,
            tipo=mov_tipo,
            cantidad=mov_cantidad,
            fecha_hora=fecha_hora,
            personal_id=req.personal_id,
            motivo=req.motivo,
            referencia=req.referencia,
        )
        movimiento_id = self._c.mov_materiales_repo.create(mov)
        self._c.materiales_repo.update_stock(req.material_id, stock_nuevo)
        incidencia_id = self._create_incidencia_if_needed(
            req=req,
            warnings=warnings,
            fecha_hora=fecha_hora,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            movimiento_id=movimiento_id,
        )
        return incidencia_id, movimiento_id

    def _build_response(
        self,
        *,
        movimiento_id: int,
        stock_anterior: int,
        stock_nuevo: int,
        warnings: List[WarningItem],
        incidencia_id: Optional[int],
    ) -> AjustarStockMaterialResult:
        return AjustarStockMaterialResult(
            movimiento_id=movimiento_id,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            warnings=warnings,
            incidencia_id=incidencia_id,
        )

    def _next_stock(self, tipo: str, stock_anterior: int, cantidad: int) -> int:
        if tipo == "ENTRADA":
            stock_nuevo = stock_anterior + cantidad
        elif tipo == "SALIDA":
            stock_nuevo = stock_anterior - cantidad
        else:
            stock_nuevo = cantidad
        if stock_nuevo < 0:
            raise ValidationError("La operación dejaría el stock en negativo (no permitido).")
        return stock_nuevo

    def _build_warnings(
        self, req: AjustarStockMaterialRequest, stock_anterior: int, stock_nuevo: int
    ) -> List[WarningItem]:
        warnings: List[WarningItem] = []
        umbral_grande = 100
        if req.tipo in ("ENTRADA", "SALIDA") and req.cantidad >= umbral_grande:
            warnings.append(
                WarningItem(
                    codigo="MOVIMIENTO_GRANDE",
                    mensaje=f"Movimiento grande ({req.tipo} de {req.cantidad}). Revisar si es correcto.",
                    severidad="MEDIA",
                )
            )
        if req.tipo == "AJUSTE" and abs(stock_nuevo - stock_anterior) >= umbral_grande:
            warnings.append(
                WarningItem(
                    codigo="AJUSTE_GRANDE",
                    mensaje=f"Ajuste grande (de {stock_anterior} a {stock_nuevo}). Revisar si es correcto.",
                    severidad="ALTA",
                )
            )
        return warnings

    def _validate_override(self, req: AjustarStockMaterialRequest, warnings: List[WarningItem]) -> None:
        if not warnings:
            return
        if not req.override:
            raise PendingWarningsError(warnings)
        if not req.nota_override or not req.nota_override.strip():
            raise ValidationError("nota_override obligatoria al guardar con warning.")
        if not req.confirmado_por_personal_id or req.confirmado_por_personal_id <= 0:
            raise ValidationError("confirmado_por_personal_id obligatorio.")

    def _resolve_movement(self, req: AjustarStockMaterialRequest, stock_anterior: int, stock_nuevo: int) -> Tuple[str, int]:
        if req.tipo != "AJUSTE":
            return req.tipo, req.cantidad
        delta = stock_nuevo - stock_anterior
        if delta == 0:
            raise ValidationError("AJUSTE sin cambio real de stock (no permitido).")
        return "AJUSTE", delta

    def _create_incidencia_if_needed(
        self,
        *,
        req: AjustarStockMaterialRequest,
        warnings: List[WarningItem],
        fecha_hora: str,
        stock_anterior: int,
        stock_nuevo: int,
        movimiento_id: int,
    ) -> Optional[int]:
        if not warnings:
            return None
        from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia

        inc = Incidencia(
            tipo="STOCK",
            severidad=self._max_severidad(warnings),
            estado="ABIERTA",
            fecha_hora=fecha_hora,
            descripcion=self._build_incidencia_descripcion(
                req, warnings, fecha_hora, stock_anterior, stock_nuevo, movimiento_id
            ),
            medico_id=None,
            personal_id=req.personal_id,
            cita_id=None,
            dispensacion_id=None,
            receta_id=None,
            confirmado_por_personal_id=req.confirmado_por_personal_id or 0,
            nota_override=req.nota_override.strip(),
        )
        return self._c.incidencias_repo.create(inc)

    # -----------------------------------------------------------------
    # Internos
    # -----------------------------------------------------------------

    def _max_severidad(self, warnings: List[WarningItem]) -> str:
        order = {"BAJA": 1, "MEDIA": 2, "ALTA": 3}
        return max((w.severidad for w in warnings), key=lambda s: order.get(s, 0))

    def _build_incidencia_descripcion(
        self,
        req: AjustarStockMaterialRequest,
        warnings: List[WarningItem],
        fecha_hora: str,
        stock_anterior: int,
        stock_nuevo: int,
        movimiento_id: int,
    ) -> str:
        warn_lines = "\n".join([f"- [{w.severidad}] {w.codigo}: {w.mensaje}" for w in warnings])
        return (
            "Ajuste de stock de material registrado con override.\n"
            f"Movimiento ID: {movimiento_id}\n"
            f"Material ID: {req.material_id}\n"
            f"Tipo: {req.tipo}\n"
            f"Cantidad: {req.cantidad}\n"
            f"Stock anterior: {stock_anterior}\n"
            f"Stock nuevo: {stock_nuevo}\n"
            f"Personal ID: {req.personal_id}\n"
            f"FechaHora: {fecha_hora}\n"
            "Warnings:\n"
            f"{warn_lines}"
        )

    def _now_iso(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat(sep=" ")
