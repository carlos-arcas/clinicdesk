from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.queries.historial_paciente_queries import CitaHistorialRow
from clinicdesk.app.queries.recetas_queries import RecetaPacienteFlatRow


class PacienteDetalleGateway(Protocol):
    def get_by_id(self, paciente_id: int) -> Paciente | None:
        ...


class HistorialCitasGateway(Protocol):
    def listar_citas_por_paciente(self, paciente_id: int, *, limite: int = 200) -> list[CitaHistorialRow]:
        ...


class HistorialRecetasGateway(Protocol):
    def list_flat_por_paciente(self, paciente_id: int) -> list[RecetaPacienteFlatRow]:
        ...


@dataclass(frozen=True, slots=True)
class RecetaResumen:
    id: int
    fecha: str
    medico: str
    estado: str
    num_lineas: int
    activa: bool


@dataclass(frozen=True, slots=True)
class LineaRecetaResumen:
    receta_id: int
    linea_id: int
    medicamento: str
    posologia: str
    inicio: str
    fin: str
    estado: str


@dataclass(frozen=True, slots=True)
class HistorialPacienteResultado:
    paciente_detalle: Paciente
    citas: tuple[CitaHistorialRow, ...]
    recetas: tuple[RecetaResumen, ...]
    detalle_por_receta: dict[int, tuple[LineaRecetaResumen, ...]]
    filtro_activas_habilitado: bool
    filtro_activas_tooltip: str | None


class ObtenerHistorialPaciente:
    def __init__(
        self,
        pacientes_gateway: PacienteDetalleGateway,
        citas_gateway: HistorialCitasGateway,
        recetas_gateway: HistorialRecetasGateway,
    ) -> None:
        self._pacientes_gateway = pacientes_gateway
        self._citas_gateway = citas_gateway
        self._recetas_gateway = recetas_gateway

    def execute(self, paciente_id: int) -> HistorialPacienteResultado | None:
        paciente = self._pacientes_gateway.get_by_id(paciente_id)
        if paciente is None:
            return None
        citas = self._citas_gateway.listar_citas_por_paciente(paciente_id)
        recetas, detalle = self._armar_recetas(self._recetas_gateway.list_flat_por_paciente(paciente_id))
        return HistorialPacienteResultado(
            paciente_detalle=paciente,
            citas=tuple(citas),
            recetas=tuple(recetas),
            detalle_por_receta=detalle,
            filtro_activas_habilitado=True,
            filtro_activas_tooltip=None,
        )

    def _armar_recetas(
        self,
        rows: list[RecetaPacienteFlatRow],
    ) -> tuple[list[RecetaResumen], dict[int, tuple[LineaRecetaResumen, ...]]]:
        recetas_map: dict[int, RecetaResumen] = {}
        lineas_map: dict[int, list[LineaRecetaResumen]] = {}
        for row in rows:
            lineas = lineas_map.setdefault(row.receta_id, [])
            if row.linea_id is not None:
                lineas.append(self._map_linea(row))
            if row.receta_id in recetas_map:
                continue
            recetas_map[row.receta_id] = RecetaResumen(
                id=row.receta_id,
                fecha=row.receta_fecha,
                medico=row.medico_nombre,
                estado=row.receta_estado,
                num_lineas=0,
                activa=False,
            )

        recetas = [self._actualizar_resumen(recetas_map[receta_id], lineas_map.get(receta_id, [])) for receta_id in recetas_map]
        detalle = {receta_id: tuple(lineas) for receta_id, lineas in lineas_map.items()}
        return recetas, detalle

    def _actualizar_resumen(self, receta: RecetaResumen, lineas: list[LineaRecetaResumen]) -> RecetaResumen:
        activa = _derivar_receta_activa(receta.estado, lineas)
        return RecetaResumen(
            id=receta.id,
            fecha=receta.fecha,
            medico=receta.medico,
            estado=receta.estado,
            num_lineas=len(lineas),
            activa=activa,
        )

    def _map_linea(self, row: RecetaPacienteFlatRow) -> LineaRecetaResumen:
        assert row.linea_id is not None
        return LineaRecetaResumen(
            receta_id=row.receta_id,
            linea_id=row.linea_id,
            medicamento=row.medicamento_nombre or "",
            posologia=_format_posologia(row),
            inicio="—",
            fin=_format_fin(row),
            estado=row.linea_estado or "",
        )


def _format_posologia(row: RecetaPacienteFlatRow) -> str:
    dosis = (row.linea_dosis or "").strip()
    if row.linea_cantidad is None:
        return dosis
    return f"{dosis} · {row.linea_cantidad}"


def _format_fin(row: RecetaPacienteFlatRow) -> str:
    if row.linea_duracion_dias is None:
        return "—"
    return f"{row.linea_duracion_dias} d"


def _derivar_receta_activa(estado_receta: str, lineas: list[LineaRecetaResumen]) -> bool:
    estado = estado_receta.strip().upper()
    if estado in {"ANULADA", "CANCELADA", "FINALIZADA", "DISPENSADA"}:
        return False
    if not lineas:
        return estado in {"ACTIVA", "PENDIENTE"}
    return any(_linea_activa(linea) for linea in lineas)


def _linea_activa(linea: LineaRecetaResumen) -> bool:
    estado = linea.estado.strip().upper()
    return estado not in {"ANULADA", "DISPENSADA", "FINALIZADA", "CANCELADA"}
