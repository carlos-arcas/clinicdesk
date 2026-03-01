from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    CitaPendienteCierreDTO,
    ListadoCitasPendientesCierreDTO,
    ResultadoCierreCitasDTO,
)
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries

LOGGER = get_logger(__name__)

ESTADOS_FINALES_PERMITIDOS = frozenset({"REALIZADA", "NO_PRESENTADO", "CANCELADA"})
ESTADO_DEJAR_IGUAL = "DEJAR_IGUAL"


class CierreCitasPendientesError(ValueError):
    def __init__(self, mensaje_i18n_key: str) -> None:
        super().__init__(mensaje_i18n_key)
        self.mensaje_i18n_key = mensaje_i18n_key


@dataclass(frozen=True, slots=True)
class CierreCitaItemRequest:
    cita_id: int
    nuevo_estado: str


@dataclass(frozen=True, slots=True)
class CerrarCitasPendientesRequest:
    items: list[CierreCitaItemRequest]


@dataclass(frozen=True, slots=True)
class PaginacionPendientesCierre:
    limite: int = 50
    offset: int = 0


class ListarCitasPendientesCierre:
    def __init__(self, queries: PrediccionAusenciasQueries) -> None:
        self._queries = queries

    def ejecutar(self, paginacion: PaginacionPendientesCierre) -> ListadoCitasPendientesCierreDTO:
        items, total = self._queries.listar_citas_pendientes_cierre(
            limite=paginacion.limite,
            offset=paginacion.offset,
        )
        return ListadoCitasPendientesCierreDTO(
            items=[
                CitaPendienteCierreDTO(
                    cita_id=item.cita_id,
                    inicio_local=item.inicio_local,
                    paciente=item.paciente,
                    medico=item.medico,
                    estado_actual=item.estado_actual,
                )
                for item in items
            ],
            total=total,
        )


class CerrarCitasPendientes:
    def __init__(self, queries: PrediccionAusenciasQueries) -> None:
        self._queries = queries

    def ejecutar(self, request: CerrarCitasPendientesRequest) -> ResultadoCierreCitasDTO:
        items_validos, ignoradas = self._filtrar_items(request.items)
        if not items_validos:
            return ResultadoCierreCitasDTO(actualizadas=0, ignoradas=ignoradas, errores=0)
        try:
            actualizadas = self._queries.cerrar_citas_en_lote(items_validos)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "prediccion_cierre_citas_fallido",
                extra={"reason_code": "save_failed", "error": str(exc), "total_items": len(items_validos)},
            )
            raise CierreCitasPendientesError("prediccion_ausencias.cierre.error_guardado") from exc
        return ResultadoCierreCitasDTO(actualizadas=actualizadas, ignoradas=ignoradas, errores=0)

    def _filtrar_items(self, items: list[CierreCitaItemRequest]) -> tuple[list[tuple[int, str]], int]:
        validos: list[tuple[int, str]] = []
        ignoradas = 0
        for item in items:
            if item.nuevo_estado == ESTADO_DEJAR_IGUAL:
                ignoradas += 1
                continue
            self._validar_estado(item.nuevo_estado)
            validos.append((item.cita_id, item.nuevo_estado))
        return validos, ignoradas

    @staticmethod
    def _validar_estado(nuevo_estado: str) -> None:
        if nuevo_estado not in ESTADOS_FINALES_PERMITIDOS:
            raise CierreCitasPendientesError("prediccion_ausencias.cierre.error_estado_invalido")
