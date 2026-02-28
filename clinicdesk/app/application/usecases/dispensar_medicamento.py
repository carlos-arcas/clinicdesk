# application/usecases/dispensar_medicamento.py
"""
Caso de uso: Dispensar medicamento.

Reglas:
- Validaciones duras (NO override):
  - Receta inexistente
  - Línea inexistente o no pertenece a la receta
  - Medicamento inexistente/inactivo
  - Stock insuficiente (no se puede dejar negativo)
  - Cantidad inválida

- Validaciones blandas (warnings):
  - Personal sin cuadrante cargado ese día
  - Personal con ausencia que solapa
  - (Opcional) Personal no previsto trabajando: si no hay bloque de calendario ese día (warning)

- Guardado consciente:
  - Si hay warnings, no se guarda salvo override=True, nota_override obligatoria,
    confirmado_por_personal_id obligatorio.
  - Si se guarda con override:
      - la dispensación se marca con incidencia=True y notas_incidencia
      - se crea incidencia en tabla incidencias (tipo=DISPENSACION)

Efectos:
- Inserta dispensación
- Actualiza stock de medicamento
- Inserta movimiento en movimientos_medicamentos (tipo=SALIDA)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.container import AppContainer


# ---------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------


@dataclass(slots=True)
class WarningItem:
    codigo: str
    mensaje: str
    severidad: str  # "BAJA" | "MEDIA" | "ALTA"


class PendingWarningsError(ValidationError):
    """
    Se lanza cuando hay warnings y no se ha indicado override.
    """

    def __init__(self, warnings: List[WarningItem]) -> None:
        super().__init__("La operación requiere confirmación (override) por incidencias/warnings.")
        self.warnings = warnings


@dataclass(slots=True)
class DispensarMedicamentoRequest:
    receta_id: int
    receta_linea_id: int
    personal_id: int

    cantidad: int

    # Si no se indica, se usa el medicamento de la línea de receta
    medicamento_id: Optional[int] = None

    # Si no se indica, se usa now()
    fecha_hora: Optional[str] = None  # ISO "YYYY-MM-DD HH:MM:SS"

    override: bool = False
    nota_override: Optional[str] = None
    confirmado_por_personal_id: Optional[int] = None  # quién autoriza el override


@dataclass(slots=True)
class DispensarMedicamentoResult:
    dispensacion_id: int
    movimiento_id: int
    stock_nuevo: int
    warnings: List[WarningItem]
    incidencia_id: Optional[int]


@dataclass(frozen=True, slots=True)
class _DispenseState:
    fecha_hora: str
    fecha: str
    medicamento_id: int
    stock_nuevo: int


# ---------------------------------------------------------------------
# Use case
# ---------------------------------------------------------------------




def _max_severidad(warnings: List[WarningItem]) -> str:
    order = {"BAJA": 1, "MEDIA": 2, "ALTA": 3}
    return max((w.severidad for w in warnings), key=lambda sev: order.get(sev, 0))


def _build_incidencia_descripcion(
    req: DispensarMedicamentoRequest,
    warnings: List[WarningItem],
    fecha_hora: str,
    medicamento_id: int,
    dispensacion_id: int,
) -> str:
    warn_lines = "\n".join([f"- [{w.severidad}] {w.codigo}: {w.mensaje}" for w in warnings])
    return (
        "Dispensación registrada con override.\n"
        f"Dispensación ID: {dispensacion_id}\n"
        f"Receta ID: {req.receta_id}\n"
        f"Línea ID: {req.receta_linea_id}\n"
        f"Medicamento ID: {medicamento_id}\n"
        f"Personal ID: {req.personal_id}\n"
        f"Cantidad: {req.cantidad}\n"
        f"FechaHora: {fecha_hora}\n"
        "Warnings:\n"
        f"{warn_lines}"
    )


class DispensarMedicamentoUseCase:
    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def execute(self, req: DispensarMedicamentoRequest) -> DispensarMedicamentoResult:
        self._c.user_context.require_write("farmacia.dispensar")
        self._validate_request(req)
        state = self._load_state(req)
        warnings, incidencia_flag, notas_incidencia = self._compute_changes(req, state)
        dispensacion_id, movimiento_id, incidencia_id = self._persist(
            req=req,
            state=state,
            warnings=warnings,
            incidencia_flag=incidencia_flag,
            notas_incidencia=notas_incidencia,
        )
        return self._build_response(
            dispensacion_id=dispensacion_id,
            movimiento_id=movimiento_id,
            stock_nuevo=state.stock_nuevo,
            warnings=warnings,
            incidencia_id=incidencia_id,
        )

    def _validate_request(self, req: DispensarMedicamentoRequest) -> None:
        if req.receta_id <= 0:
            raise ValidationError("receta_id inválido.")
        if req.receta_linea_id <= 0:
            raise ValidationError("receta_linea_id inválido.")
        if req.personal_id <= 0:
            raise ValidationError("personal_id inválido.")
        if req.cantidad <= 0:
            raise ValidationError("cantidad debe ser mayor que 0.")

    def _load_state(self, req: DispensarMedicamentoRequest) -> _DispenseState:
        fecha_hora = req.fecha_hora or self._now_iso()
        fecha = fecha_hora[:10]
        receta = self._c.recetas_repo.get_receta_by_id(req.receta_id)
        if not receta:
            raise ValidationError("La receta no existe.")
        linea = self._get_linea_or_fail(req)
        medicamento_id, stock_actual = self._resolve_medicamento_id(req, linea)
        stock_nuevo = self._compute_stock_nuevo(stock_actual, req.cantidad)
        return _DispenseState(
            fecha_hora=fecha_hora,
            fecha=fecha,
            medicamento_id=medicamento_id,
            stock_nuevo=stock_nuevo,
        )

    def _compute_changes(
        self, req: DispensarMedicamentoRequest, state: _DispenseState
    ) -> Tuple[List[WarningItem], bool, Optional[str]]:
        warnings = self._collect_warnings(req, state)
        self._validate_override(req, warnings)
        if not warnings:
            return warnings, False, None
        return warnings, True, req.nota_override.strip() if req.nota_override else None

    def _persist(
        self,
        *,
        req: DispensarMedicamentoRequest,
        state: _DispenseState,
        warnings: List[WarningItem],
        incidencia_flag: bool,
        notas_incidencia: Optional[str],
    ) -> Tuple[int, int, Optional[int]]:
        from clinicdesk.app.infrastructure.sqlite.repos_dispensaciones import Dispensacion

        disp = Dispensacion(
            receta_id=req.receta_id,
            receta_linea_id=req.receta_linea_id,
            medicamento_id=state.medicamento_id,
            personal_id=req.personal_id,
            cantidad=req.cantidad,
            fecha_hora=state.fecha_hora,
            incidencia=incidencia_flag,
            notas_incidencia=notas_incidencia,
        )
        dispensacion_id = self._c.dispensaciones_repo.create(disp)
        self._c.medicamentos_repo.update_stock(state.medicamento_id, state.stock_nuevo)
        movimiento_id = self._create_movement(req, state, dispensacion_id)
        incidencia_id = self._create_incidencia_if_needed(req, state, warnings, dispensacion_id)
        return dispensacion_id, movimiento_id, incidencia_id

    def _build_response(
        self,
        *,
        dispensacion_id: int,
        movimiento_id: int,
        stock_nuevo: int,
        warnings: List[WarningItem],
        incidencia_id: Optional[int],
    ) -> DispensarMedicamentoResult:
        return DispensarMedicamentoResult(
            dispensacion_id=dispensacion_id,
            movimiento_id=movimiento_id,
            stock_nuevo=stock_nuevo,
            warnings=warnings,
            incidencia_id=incidencia_id,
        )

    def _get_linea_or_fail(self, req: DispensarMedicamentoRequest):
        linea = self._get_linea_by_id(req.receta_linea_id)
        if not linea:
            raise ValidationError("La línea de receta no existe.")
        if linea["receta_id"] != req.receta_id:
            raise ValidationError("La línea no pertenece a la receta indicada.")
        return linea

    def _resolve_medicamento_id(self, req: DispensarMedicamentoRequest, linea) -> Tuple[int, int]:
        linea_medicamento_id = int(linea["medicamento_id"])
        if req.medicamento_id and linea_medicamento_id != req.medicamento_id:
            raise ValidationError("medicamento_id no coincide con el de la línea de receta.")
        medicamento_id = req.medicamento_id or linea_medicamento_id
        medicamento = self._c.medicamentos_repo.get_by_id(medicamento_id)
        if not medicamento or not medicamento.activo:
            raise ValidationError("El medicamento no existe o está inactivo.")
        return medicamento_id, int(medicamento.cantidad_en_almacen)

    def _compute_stock_nuevo(self, stock_actual: int, cantidad: int) -> int:
        stock_nuevo = stock_actual - cantidad
        if stock_nuevo < 0:
            raise ValidationError(
                f"Stock insuficiente. Stock actual={stock_actual}, solicitado={cantidad}."
            )
        return stock_nuevo

    def _collect_warnings(self, req: DispensarMedicamentoRequest, state: _DispenseState) -> List[WarningItem]:
        warnings: List[WarningItem] = []
        hay_calendario = self._c.calendario_personal_repo.exists_for_personal_fecha(
            req.personal_id, state.fecha, solo_activos=True
        )
        if not hay_calendario:
            warnings.append(
                WarningItem(
                    codigo="PERSONAL_SIN_CUADRANTE",
                    mensaje="No hay cuadrante cargado para el personal en esa fecha. Se permite guardar bajo confirmación.",
                    severidad="MEDIA",
                )
            )
        if self._c.ausencias_personal_repo.exists_overlap(req.personal_id, state.fecha_hora, state.fecha_hora):
            warnings.append(
                WarningItem(
                    codigo="PERSONAL_CON_AUSENCIA",
                    mensaje="El personal tiene una ausencia que solapa con la dispensación. Normalmente no se debe registrar.",
                    severidad="ALTA",
                )
            )
        return warnings

    def _validate_override(self, req: DispensarMedicamentoRequest, warnings: List[WarningItem]) -> None:
        if not warnings:
            return
        if not req.override:
            raise PendingWarningsError(warnings)
        if not req.nota_override or not req.nota_override.strip():
            raise ValidationError("Para guardar con incidencia/warning es obligatorio rellenar nota_override.")
        if not req.confirmado_por_personal_id or req.confirmado_por_personal_id <= 0:
            raise ValidationError("confirmado_por_personal_id es obligatorio al guardar con override.")

    def _create_movement(self, req: DispensarMedicamentoRequest, state: _DispenseState, dispensacion_id: int) -> int:
        from clinicdesk.app.infrastructure.sqlite.repos_movimientos_medicamentos import MovimientoMedicamento

        mov = MovimientoMedicamento(
            medicamento_id=state.medicamento_id,
            tipo="SALIDA",
            cantidad=req.cantidad,
            fecha_hora=state.fecha_hora,
            personal_id=req.personal_id,
            motivo="DISPENSACION",
            referencia=f"dispensacion:{dispensacion_id};receta:{req.receta_id};linea:{req.receta_linea_id}",
        )
        return self._c.mov_medicamentos_repo.create(mov)

    def _create_incidencia_if_needed(
        self,
        req: DispensarMedicamentoRequest,
        state: _DispenseState,
        warnings: List[WarningItem],
        dispensacion_id: int,
    ) -> Optional[int]:
        if not warnings:
            return None
        from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia

        inc = Incidencia(
            tipo="DISPENSACION",
            severidad=_max_severidad(warnings),
            estado="ABIERTA",
            fecha_hora=state.fecha_hora,
            descripcion=_build_incidencia_descripcion(
                req, warnings, state.fecha_hora, state.medicamento_id, dispensacion_id
            ),
            medico_id=None,
            personal_id=req.personal_id,
            cita_id=None,
            dispensacion_id=dispensacion_id,
            receta_id=req.receta_id,
            confirmado_por_personal_id=req.confirmado_por_personal_id or 0,
            nota_override=req.nota_override.strip() if req.nota_override else "",
        )
        return self._c.incidencias_repo.create(inc)

    # -----------------------------------------------------------------
    # Internos
    # -----------------------------------------------------------------

    def _get_linea_by_id(self, receta_linea_id: int):
        return self._c.connection.execute(
            "SELECT * FROM receta_lineas WHERE id = ?",
            (receta_linea_id,),
        ).fetchone()

    def _now_iso(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat(sep=" ")
