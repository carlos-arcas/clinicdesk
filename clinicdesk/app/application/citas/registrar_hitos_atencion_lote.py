from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from clinicdesk.app.application.citas.registrar_hito_atencion import (
    CitasHitosRepositorioPuerto,
    HitoAtencion,
    RegistrarHitoAtencionCita,
)
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


class ModoTimestampHito(str, Enum):
    AHORA = "AHORA"
    PROGRAMADA = "PROGRAMADA"


ModoTimestamp: TypeAlias = ModoTimestampHito


@dataclass(frozen=True, slots=True)
class RegistrarHitosLoteError(Exception):
    reason_code: str

    def __str__(self) -> str:
        return self.reason_code


@dataclass(slots=True)
class ResultadoLoteHitosDTO:
    total: int = 0
    aplicadas: int = 0
    ya_estaban: int = 0
    omitidas_por_orden: int = 0
    no_encontradas: int = 0
    no_permitido_programada: int = 0
    errores: int = 0


@dataclass(frozen=True, slots=True)
class RegistrarHitosAtencionEnLote:
    registrar_hito_uc: RegistrarHitoAtencionCita
    repositorio: CitasHitosRepositorioPuerto

    def ejecutar(
        self, cita_ids: tuple[int, ...], hito: HitoAtencion, modo_timestamp: ModoTimestampHito
    ) -> ResultadoLoteHitosDTO:
        if modo_timestamp is ModoTimestampHito.PROGRAMADA and hito not in _HITOS_CON_PROGRAMADA:
            raise RegistrarHitosLoteError("modo_programada_no_permitido")

        dto = ResultadoLoteHitosDTO(total=len(cita_ids))
        marcas_programadas = self._cargar_marcas_programadas(cita_ids, modo_timestamp)
        for cita_id in cita_ids:
            marca_tiempo = self._resolver_marca_tiempo(cita_id, modo_timestamp, marcas_programadas, dto)
            if modo_timestamp is ModoTimestampHito.PROGRAMADA and marca_tiempo is None:
                continue
            self._acumular_resultado(dto, cita_id, hito, marca_tiempo)

        self._log_resumen(hito, modo_timestamp, dto)
        return dto

    def _cargar_marcas_programadas(
        self, cita_ids: tuple[int, ...], modo_timestamp: ModoTimestampHito
    ) -> dict[int, datetime]:
        if modo_timestamp is not ModoTimestampHito.PROGRAMADA or not cita_ids:
            return {}
        return self.repositorio.obtener_inicios_programados_por_cita_ids(cita_ids)

    def _resolver_marca_tiempo(
        self,
        cita_id: int,
        modo_timestamp: ModoTimestampHito,
        marcas_programadas: dict[int, datetime],
        dto: ResultadoLoteHitosDTO,
    ) -> datetime | None:
        if modo_timestamp is ModoTimestampHito.AHORA:
            return None
        marca = marcas_programadas.get(cita_id)
        if marca is not None:
            return marca
        if self.repositorio.obtener_cita_por_id(cita_id) is None:
            dto.no_encontradas += 1
            return None
        raise RegistrarHitosLoteError("datos_programada_no_disponibles")

    def _acumular_resultado(
        self,
        dto: ResultadoLoteHitosDTO,
        cita_id: int,
        hito: HitoAtencion,
        marca_tiempo: datetime | None,
    ) -> None:
        try:
            resultado = self.registrar_hito_uc.ejecutar(cita_id, hito, marca_tiempo)
        except RegistrarHitosLoteError:
            raise
        except Exception as exc:
            LOGGER.exception("citas_hitos_lote_error", extra={"action": "citas_hitos_lote_error", "hito": hito.value})
            raise RegistrarHitosLoteError("unexpected_error") from exc

        if resultado.aplicado:
            dto.aplicadas += 1
        elif resultado.ya_estaba:
            dto.ya_estaban += 1
        elif resultado.reason_code.startswith("orden_invalido"):
            dto.omitidas_por_orden += 1
        elif resultado.reason_code == "cita_no_encontrada":
            dto.no_encontradas += 1
        else:
            dto.errores += 1

    def _log_resumen(self, hito: HitoAtencion, modo_timestamp: ModoTimestampHito, dto: ResultadoLoteHitosDTO) -> None:
        LOGGER.info(
            "citas_hitos_lote",
            extra={
                "action": "citas_hitos_lote",
                "hito": hito.value,
                "modo": modo_timestamp.value,
                "total": dto.total,
                "aplicadas": dto.aplicadas,
                "omitidas_por_orden": dto.omitidas_por_orden,
                "errores": dto.errores,
            },
        )


_HITOS_CON_PROGRAMADA = {HitoAtencion.CHECK_IN, HitoAtencion.INICIO_CONSULTA}
