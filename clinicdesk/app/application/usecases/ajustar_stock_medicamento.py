# application/usecases/ajustar_stock_medicamento.py
"""
Caso de uso: Ajustar stock de medicamento (ENTRADA / SALIDA / AJUSTE).

Objetivo:
- Unificar la operación de stock para auditoría:
  - Actualiza stock actual (tabla medicamentos)
  - Inserta movimiento (movimientos_medicamentos)

Reglas:
- Duro (NO override):
  - Medicamento inexistente/inactivo
  - cantidad inválida (0)
  - SALIDA no puede dejar stock negativo

- Warnings (requieren guardado consciente):
  - AJUSTE con magnitud grande (posible error)
  - SALIDA grande (posible error)
  - ENTRADA grande (posible error)

Guardado consciente:
- Si hay warnings, no guarda salvo override=True y nota_override obligatoria
  y confirmado_por_personal_id obligatorio.
- Si se guarda con override, se crea incidencia (tipo=STOCK).

Notas:
- cantidad siempre es un entero. Para SALIDA se aplica como resta.
- El movimiento se guarda con cantidad positiva, y el campo tipo indica la dirección.
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
class AjustarStockMedicamentoRequest:
    medicamento_id: int
    tipo: str                 # "ENTRADA" | "SALIDA" | "AJUSTE"
    cantidad: int             # magnitud (>0)
    personal_id: int          # quien ejecuta la operación

    motivo: Optional[str] = None
    referencia: Optional[str] = None
    fecha_hora: Optional[str] = None  # ISO "YYYY-MM-DD HH:MM:SS"

    override: bool = False
    nota_override: Optional[str] = None
    confirmado_por_personal_id: Optional[int] = None  # quien autoriza el override


@dataclass(slots=True)
class AjustarStockMedicamentoResult:
    movimiento_id: int
    stock_anterior: int
    stock_nuevo: int
    warnings: List[WarningItem]
    incidencia_id: Optional[int]


# ---------------------------------------------------------------------
# Use case
# ---------------------------------------------------------------------


class AjustarStockMedicamentoUseCase:
    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def execute(self, req: AjustarStockMedicamentoRequest) -> AjustarStockMedicamentoResult:
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

    def _validate_request(self, req: AjustarStockMedicamentoRequest) -> None:
        if req.medicamento_id <= 0:
            raise ValidationError("medicamento_id inválido.")
        if req.personal_id <= 0:
            raise ValidationError("personal_id inválido.")
        if req.cantidad <= 0:
            raise ValidationError("cantidad debe ser mayor que 0.")
        if req.tipo not in ("ENTRADA", "SALIDA", "AJUSTE"):
            raise ValidationError("tipo debe ser ENTRADA, SALIDA o AJUSTE.")

    def _load_state(self, req: AjustarStockMedicamentoRequest) -> Tuple[str, int]:
        fecha_hora = req.fecha_hora or self._now_iso()
        medicamento = self._c.medicamentos_repo.get_by_id(req.medicamento_id)
        if not medicamento or not medicamento.activo:
            raise ValidationError("El medicamento no existe o está inactivo.")
        return fecha_hora, int(medicamento.cantidad_en_almacen)

    def _compute_changes(self, req: AjustarStockMedicamentoRequest, stock_anterior: int) -> Tuple[int, List[WarningItem], str, int]:
        stock_nuevo = self._next_stock(req.tipo, stock_anterior, req.cantidad)
        warnings = self._build_warnings(req, stock_anterior, stock_nuevo)
        self._validate_override(req, warnings)
        mov_tipo, mov_cantidad = self._resolve_movement(req, stock_anterior, stock_nuevo)
        return stock_nuevo, warnings, mov_tipo, mov_cantidad

    def _persist(
        self,
        *,
        req: AjustarStockMedicamentoRequest,
        fecha_hora: str,
        stock_anterior: int,
        stock_nuevo: int,
        warnings: List[WarningItem],
        mov_tipo: str,
        mov_cantidad: int,
    ) -> Tuple[Optional[int], int]:
        from clinicdesk.app.infrastructure.sqlite.repos_movimientos_medicamentos import MovimientoMedicamento

        mov = MovimientoMedicamento(
            medicamento_id=req.medicamento_id,
            tipo=mov_tipo,
            cantidad=mov_cantidad,
            fecha_hora=fecha_hora,
            personal_id=req.personal_id,
            motivo=req.motivo,
            referencia=req.referencia,
        )
        movimiento_id = self._c.mov_medicamentos_repo.create(mov)
        self._c.medicamentos_repo.update_stock(req.medicamento_id, stock_nuevo)
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
    ) -> AjustarStockMedicamentoResult:
        return AjustarStockMedicamentoResult(
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
        self, req: AjustarStockMedicamentoRequest, stock_anterior: int, stock_nuevo: int
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

    def _validate_override(self, req: AjustarStockMedicamentoRequest, warnings: List[WarningItem]) -> None:
        if not warnings:
            return
        if not req.override:
            raise PendingWarningsError(warnings)
        if not req.nota_override or not req.nota_override.strip():
            raise ValidationError("Para guardar con warning es obligatorio nota_override.")
        if not req.confirmado_por_personal_id or req.confirmado_por_personal_id <= 0:
            raise ValidationError("confirmado_por_personal_id es obligatorio al guardar con override.")

    def _resolve_movement(self, req: AjustarStockMedicamentoRequest, stock_anterior: int, stock_nuevo: int) -> Tuple[str, int]:
        if req.tipo != "AJUSTE":
            return req.tipo, req.cantidad
        delta = stock_nuevo - stock_anterior
        if delta == 0:
            raise ValidationError("AJUSTE sin cambio real de stock (no permitido).")
        return "AJUSTE", delta

    def _create_incidencia_if_needed(
        self,
        *,
        req: AjustarStockMedicamentoRequest,
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
            nota_override=req.nota_override.strip() if req.nota_override else "",
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
        req: AjustarStockMedicamentoRequest,
        warnings: List[WarningItem],
        fecha_hora: str,
        stock_anterior: int,
        stock_nuevo: int,
        movimiento_id: int,
    ) -> str:
        warn_lines = "\n".join([f"- [{w.severidad}] {w.codigo}: {w.mensaje}" for w in warnings])
        return (
            "Ajuste de stock registrado con override.\n"
            f"Movimiento ID: {movimiento_id}\n"
            f"Medicamento ID: {req.medicamento_id}\n"
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
