from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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


@dataclass(frozen=True, slots=True)
class ResultadoLoteHitosDTO:
    aplicadas: int = 0
    ya_estaban: int = 0
    omitidas_por_orden: int = 0
    errores: int = 0


@dataclass(frozen=True, slots=True)
class RegistrarHitosAtencionEnLote:
    registrar_hito_uc: RegistrarHitoAtencionCita
    repositorio: CitasHitosRepositorioPuerto

    def ejecutar(self, cita_ids: tuple[int, ...], hito: HitoAtencion, modo_timestamp: ModoTimestampHito) -> ResultadoLoteHitosDTO:
        marcas_programadas = self._cargar_marcas_programadas(cita_ids, hito, modo_timestamp)
        aplicadas, ya_estaban, omitidas_por_orden, errores = 0, 0, 0, 0
        for cita_id in cita_ids:
            resultado = self.registrar_hito_uc.ejecutar(cita_id, hito, marcas_programadas.get(cita_id))
            if resultado.aplicado:
                aplicadas += 1
                continue
            if resultado.ya_estaba:
                ya_estaban += 1
                continue
            if resultado.reason_code.startswith("orden_invalido"):
                omitidas_por_orden += 1
                continue
            errores += 1
        dto = ResultadoLoteHitosDTO(
            aplicadas=aplicadas,
            ya_estaban=ya_estaban,
            omitidas_por_orden=omitidas_por_orden,
            errores=errores,
        )
        LOGGER.info(
            "citas_hitos_lote",
            extra={
                "action": "citas_hitos_lote",
                "hito": hito.value,
                "modo": modo_timestamp.value,
                "total": len(cita_ids),
                "aplicadas": dto.aplicadas,
                "omitidas": dto.ya_estaban + dto.omitidas_por_orden,
            },
        )
        return dto

    def _cargar_marcas_programadas(
        self,
        cita_ids: tuple[int, ...],
        hito: HitoAtencion,
        modo_timestamp: ModoTimestampHito,
    ) -> dict[int, object]:
        if modo_timestamp is not ModoTimestampHito.PROGRAMADA:
            return {}
        if hito not in {HitoAtencion.CHECK_IN, HitoAtencion.INICIO_CONSULTA}:
            return {}
        return self.repositorio.obtener_inicios_programados_por_cita_ids(cita_ids)
