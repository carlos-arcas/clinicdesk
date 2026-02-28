# application/usecases/crear_cita.py
"""
Caso de uso: Crear cita.

Reglas principales:
- Validaciones duras (no se pueden saltar):
  - Médico inexistente/inactivo
  - Sala inexistente/inactiva
  - Rango horario inválido
  - Solape con otra cita del médico o de la sala

- Validaciones blandas (warnings):
  - No hay cuadrante cargado para ese médico ese día
  - (Opcional) Cuadrante cargado pero el turno no cubre el horario (si se implementa)

- Guardado consciente:
  - Si hay warnings, no se guarda salvo override=True y nota_override no vacía.
  - Si se guarda con override, se crea una incidencia asociada (tipo=CITA).

- Ausencias (baja/vacaciones):
  - Bloqueo por defecto. Solo se permite override explícito con incidencia ALTA.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.modelos import Cita
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
    Se lanza cuando existen warnings y no se ha indicado override.
    """
    def __init__(self, warnings: List[WarningItem]) -> None:
        super().__init__("La operación requiere confirmación (override) por incidencias/warnings.")
        self.warnings = warnings


@dataclass(slots=True)
class CrearCitaRequest:
    paciente_id: int
    medico_id: int
    sala_id: int
    inicio: str  # ISO "YYYY-MM-DD HH:MM:SS"
    fin: str     # ISO "YYYY-MM-DD HH:MM:SS"
    motivo: Optional[str] = None
    observaciones: Optional[str] = None
    estado: str = "PROGRAMADA"

    override: bool = False
    nota_override: Optional[str] = None
    confirmado_por_personal_id: Optional[int] = None  # quién confirma el override


@dataclass(slots=True)
class CrearCitaResult:
    cita_id: int
    warnings: List[WarningItem]
    incidencia_id: Optional[int]


# ---------------------------------------------------------------------
# Use case
# ---------------------------------------------------------------------


class CrearCitaUseCase:
    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def execute(self, req: CrearCitaRequest) -> CrearCitaResult:
        self._c.user_context.require_write("citas.crear")
        self._validate_request(req)
        inicio_dt, fin_dt, estado, notas = self._normalize_inputs(req)
        self._load_dependencies(req)
        warnings = self._apply_rules(req)
        cita_id, incidencia_id = self._persist(
            req,
            inicio_dt=inicio_dt,
            fin_dt=fin_dt,
            estado=estado,
            notas=notas,
            warnings=warnings,
        )
        return self._build_response(cita_id=cita_id, warnings=warnings, incidencia_id=incidencia_id)

    # -----------------------------------------------------------------
    # Internos
    # -----------------------------------------------------------------

    def _validate_request(self, req: CrearCitaRequest) -> None:
        if req.paciente_id <= 0:
            raise ValidationError("paciente_id inválido.")
        if req.medico_id <= 0:
            raise ValidationError("medico_id inválido.")
        if req.sala_id <= 0:
            raise ValidationError("sala_id inválido.")

    def _normalize_inputs(self, req: CrearCitaRequest) -> Tuple[datetime, datetime, EstadoCita, Optional[str]]:
        inicio_dt, fin_dt = self._parse_inicio_fin(req.inicio, req.fin)
        return inicio_dt, fin_dt, EstadoCita(req.estado), req.observaciones

    def _load_dependencies(self, req: CrearCitaRequest) -> None:
        medico = self._c.medicos_repo.get_by_id(req.medico_id)
        if not medico or not medico.activo:
            raise ValidationError("El médico no existe o está inactivo.")

        sala = self._c.salas_repo.get_by_id(req.sala_id)
        if not sala or not sala.activa:
            raise ValidationError("La sala no existe o está inactiva.")

        self._assert_no_solape_medico(req.medico_id, req.inicio, req.fin)
        self._assert_no_solape_sala(req.sala_id, req.inicio, req.fin)

    def _apply_rules(self, req: CrearCitaRequest) -> List[WarningItem]:
        warnings: List[WarningItem] = []
        fecha = req.inicio[:10]

        hay_calendario = self._c.calendario_medico_repo.exists_for_medico_fecha(
            req.medico_id, fecha, solo_activos=True
        )
        if not hay_calendario:
            warnings.append(
                WarningItem(
                    codigo="MEDICO_SIN_CUADRANTE",
                    mensaje="No hay cuadrante cargado para el médico en esa fecha. Se permite guardar bajo confirmación.",
                    severidad="MEDIA",
                )
            )

        if self._c.ausencias_medico_repo.exists_overlap(req.medico_id, req.inicio, req.fin):
            warnings.append(
                WarningItem(
                    codigo="MEDICO_CON_AUSENCIA",
                    mensaje="El médico tiene una ausencia que solapa con el horario. Normalmente no se debe crear la cita.",
                    severidad="ALTA",
                )
            )

        if not warnings:
            return warnings
        if not req.override:
            raise PendingWarningsError(warnings)
        if not req.nota_override or not req.nota_override.strip():
            raise ValidationError("Para guardar con incidencia/warning es obligatorio rellenar nota_override.")
        if not req.confirmado_por_personal_id or req.confirmado_por_personal_id <= 0:
            raise ValidationError("confirmado_por_personal_id es obligatorio al guardar con override.")
        return warnings

    def _persist(
        self,
        req: CrearCitaRequest,
        *,
        inicio_dt: datetime,
        fin_dt: datetime,
        estado: EstadoCita,
        notas: Optional[str],
        warnings: List[WarningItem],
    ) -> Tuple[int, Optional[int]]:
        cita = Cita(
            id=None,
            paciente_id=req.paciente_id,
            medico_id=req.medico_id,
            sala_id=req.sala_id,
            inicio=inicio_dt,
            fin=fin_dt,
            motivo=req.motivo,
            notas=notas,
            estado=estado,
        )
        cita_id = self._c.citas_repo.create(cita)
        if not warnings:
            return cita_id, None

        severidad = self._max_severidad(warnings)
        descripcion = self._build_incidencia_descripcion(req, warnings, medico_id=req.medico_id, sala_id=req.sala_id)

        from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia  # modelo ligero del repo

        inc = Incidencia(
            tipo="CITA",
            severidad=severidad,
            estado="ABIERTA",
            fecha_hora=self._now_iso(),
            descripcion=descripcion,
            medico_id=req.medico_id,
            personal_id=req.confirmado_por_personal_id,
            cita_id=cita_id,
            dispensacion_id=None,
            receta_id=None,
            confirmado_por_personal_id=req.confirmado_por_personal_id,
            nota_override=req.nota_override.strip(),
        )
        return cita_id, self._c.incidencias_repo.create(inc)

    def _build_response(
        self,
        *,
        cita_id: int,
        warnings: List[WarningItem],
        incidencia_id: Optional[int],
    ) -> CrearCitaResult:
        return CrearCitaResult(cita_id=cita_id, warnings=warnings, incidencia_id=incidencia_id)

    def _parse_inicio_fin(self, inicio: str, fin: str) -> Tuple[datetime, datetime]:
        if not inicio or not fin:
            raise ValidationError("inicio y fin son obligatorios.")
        try:
            inicio_dt = datetime.fromisoformat(inicio)
            fin_dt = datetime.fromisoformat(fin)
        except ValueError as e:
            raise ValidationError(f"Formato de fecha/hora inválido: {e}") from e

        if fin_dt <= inicio_dt:
            raise ValidationError("fin debe ser posterior a inicio.")
        return inicio_dt, fin_dt

    def _assert_no_solape_medico(self, medico_id: int, inicio: str, fin: str) -> None:
        # Solape: (inicio < fin_existente) AND (fin > inicio_existente)
        row = self._c.connection.execute(
            """
            SELECT 1
            FROM citas
            WHERE medico_id = ?
              AND estado != 'CANCELADA'
              AND inicio < ?
              AND fin > ?
            LIMIT 1
            """,
            (medico_id, fin, inicio),
        ).fetchone()
        if row:
            raise ValidationError("Existe un solape con otra cita del médico (no permitido).")

    def _assert_no_solape_sala(self, sala_id: int, inicio: str, fin: str) -> None:
        row = self._c.connection.execute(
            """
            SELECT 1
            FROM citas
            WHERE sala_id = ?
              AND estado != 'CANCELADA'
              AND inicio < ?
              AND fin > ?
            LIMIT 1
            """,
            (sala_id, fin, inicio),
        ).fetchone()
        if row:
            raise ValidationError("Existe un solape con otra cita en la sala (no permitido).")

    def _max_severidad(self, warnings: List[WarningItem]) -> str:
        order = {"BAJA": 1, "MEDIA": 2, "ALTA": 3}
        return max((w.severidad for w in warnings), key=lambda s: order.get(s, 0))

    def _build_incidencia_descripcion(
        self,
        req: CrearCitaRequest,
        warnings: List[WarningItem],
        *,
        medico_id: int,
        sala_id: int,
    ) -> str:
        warn_lines = "\n".join([f"- [{w.severidad}] {w.codigo}: {w.mensaje}" for w in warnings])
        return (
            "Cita creada con override.\n"
            f"Médico ID: {medico_id}\n"
            f"Sala ID: {sala_id}\n"
            f"Inicio: {req.inicio}\n"
            f"Fin: {req.fin}\n"
            "Warnings:\n"
            f"{warn_lines}"
        )

    def _now_iso(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat(sep=" ")
