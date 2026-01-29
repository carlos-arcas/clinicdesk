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
from typing import List, Optional

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
        # ---------- Validaciones duras ----------
        if req.material_id <= 0:
            raise ValidationError("material_id inválido.")
        if req.personal_id <= 0:
            raise ValidationError("personal_id inválido.")
        if req.cantidad <= 0:
            raise ValidationError("cantidad debe ser mayor que 0.")
        if req.tipo not in ("ENTRADA", "SALIDA", "AJUSTE"):
            raise ValidationError("tipo debe ser ENTRADA, SALIDA o AJUSTE.")

        fecha_hora = req.fecha_hora or self._now_iso()

        material = self._c.materiales_repo.get_by_id(req.material_id)
        if not material or not material.activo:
            raise ValidationError("El material no existe o está inactivo.")

        stock_anterior = int(material.cantidad_en_almacen)

        if req.tipo == "ENTRADA":
            stock_nuevo = stock_anterior + req.cantidad
        elif req.tipo == "SALIDA":
            stock_nuevo = stock_anterior - req.cantidad
        else:  # AJUSTE
            stock_nuevo = req.cantidad  # valor absoluto

        if stock_nuevo < 0:
            raise ValidationError("La operación dejaría el stock en negativo (no permitido).")

        # ---------- Warnings ----------
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

        # ---------- Guardado consciente ----------
        incidencia_id: Optional[int] = None
        if warnings:
            if not req.override:
                raise PendingWarningsError(warnings)

            if not req.nota_override or not req.nota_override.strip():
                raise ValidationError("nota_override obligatoria al guardar con warning.")

            if not req.confirmado_por_personal_id or req.confirmado_por_personal_id <= 0:
                raise ValidationError("confirmado_por_personal_id obligatorio.")

        # ---------- Movimiento + stock ----------
        from clinicdesk.app.infrastructure.sqlite.repos_movimientos_materiales import MovimientoMaterial

        if req.tipo == "AJUSTE":
            delta = stock_nuevo - stock_anterior
            if delta == 0:
                raise ValidationError("AJUSTE sin cambio real de stock (no permitido).")
            mov_tipo = "AJUSTE"
            mov_cantidad = delta
        else:
            mov_tipo = req.tipo
            mov_cantidad = req.cantidad

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

        # ---------- Incidencia (si override) ----------
        if warnings:
            from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia

            severidad = self._max_severidad(warnings)
            descripcion = self._build_incidencia_descripcion(
                req, warnings, fecha_hora, stock_anterior, stock_nuevo, movimiento_id
            )

            inc = Incidencia(
                tipo="STOCK",
                severidad=severidad,
                estado="ABIERTA",
                fecha_hora=fecha_hora,
                descripcion=descripcion,
                medico_id=None,
                personal_id=req.personal_id,
                cita_id=None,
                dispensacion_id=None,
                receta_id=None,
                confirmado_por_personal_id=req.confirmado_por_personal_id or 0,
                nota_override=req.nota_override.strip(),
            )
            incidencia_id = self._c.incidencias_repo.create(inc)

        return AjustarStockMaterialResult(
            movimiento_id=movimiento_id,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            warnings=warnings,
            incidencia_id=incidencia_id,
        )

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
