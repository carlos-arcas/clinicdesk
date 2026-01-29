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
        # ---------- Validaciones duras ----------
        if req.medicamento_id <= 0:
            raise ValidationError("medicamento_id inválido.")
        if req.personal_id <= 0:
            raise ValidationError("personal_id inválido.")
        if req.cantidad <= 0:
            raise ValidationError("cantidad debe ser mayor que 0.")
        if req.tipo not in ("ENTRADA", "SALIDA", "AJUSTE"):
            raise ValidationError("tipo debe ser ENTRADA, SALIDA o AJUSTE.")

        fecha_hora = req.fecha_hora or self._now_iso()

        medicamento = self._c.medicamentos_repo.get_by_id(req.medicamento_id)
        if not medicamento or not medicamento.activo:
            raise ValidationError("El medicamento no existe o está inactivo.")

        stock_anterior = int(medicamento.cantidad_en_almacen)

        if req.tipo == "ENTRADA":
            stock_nuevo = stock_anterior + req.cantidad
        elif req.tipo == "SALIDA":
            stock_nuevo = stock_anterior - req.cantidad
        else:  # AJUSTE
            # AJUSTE se interpreta como set manual de stock a un valor absoluto.
            # Para mantener consistencia con auditoría, aquí AJUSTE significa:
            #   - cantidad = nuevo_stock (absoluto)
            stock_nuevo = req.cantidad

        if stock_nuevo < 0:
            raise ValidationError("La operación dejaría el stock en negativo (no permitido).")

        # ---------- Warnings ----------
        warnings: List[WarningItem] = []
        umbral_grande = 100  # umbral simple; luego lo parametrizas por config

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
                raise ValidationError("Para guardar con warning es obligatorio nota_override.")

            if not req.confirmado_por_personal_id or req.confirmado_por_personal_id <= 0:
                raise ValidationError("confirmado_por_personal_id es obligatorio al guardar con override.")

        # ---------- Persistencia: movimiento + stock ----------
        from clinicdesk.app.infrastructure.sqlite.repos_movimientos_medicamentos import MovimientoMedicamento

        # Para AJUSTE registramos cantidad como delta (para auditoría más informativa)
        if req.tipo == "AJUSTE":
            delta = stock_nuevo - stock_anterior
            mov_cantidad = delta if delta != 0 else 0
            # delta 0 no tiene sentido; pero ya entraría por warning/validación de cantidad
            if mov_cantidad == 0:
                raise ValidationError("AJUSTE sin cambio real de stock (no permitido).")
            mov_tipo = "AJUSTE"
        else:
            mov_tipo = req.tipo
            mov_cantidad = req.cantidad  # positivo, la dirección la da tipo

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

        # ---------- Incidencia central (si override) ----------
        if warnings:
            from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia

            severidad = self._max_severidad(warnings)
            descripcion = self._build_incidencia_descripcion(req, warnings, fecha_hora, stock_anterior, stock_nuevo, movimiento_id)

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
                nota_override=req.nota_override.strip() if req.nota_override else "",
            )
            incidencia_id = self._c.incidencias_repo.create(inc)

        return AjustarStockMedicamentoResult(
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
