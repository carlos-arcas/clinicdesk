from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


class HitoAtencion(str, Enum):
    CHECK_IN = "CHECK_IN"
    LLAMADO = "LLAMADO"
    INICIO_CONSULTA = "INICIO_CONSULTA"
    FIN_CONSULTA = "FIN_CONSULTA"
    CHECK_OUT = "CHECK_OUT"


@dataclass(frozen=True, slots=True)
class ResultadoRegistrarHitoDTO:
    aplicado: bool
    ya_estaba: bool
    reason_code: str


class RelojPuerto(Protocol):
    def ahora(self) -> datetime: ...


class CitasHitosRepositorioPuerto(Protocol):
    def obtener_cita_por_id(self, cita_id: int) -> dict[str, object] | None: ...

    def actualizar_hito_atencion(self, cita_id: int, campo_timestamp: str, valor_datetime: datetime) -> bool: ...

    def obtener_inicios_programados_por_cita_ids(self, cita_ids: tuple[int, ...]) -> dict[int, datetime]: ...


@dataclass(frozen=True, slots=True)
class RegistrarHitoAtencionCita:
    repositorio: CitasHitosRepositorioPuerto
    reloj: RelojPuerto

    def ejecutar(self, cita_id: int, hito: HitoAtencion, marca_tiempo: datetime | None = None) -> ResultadoRegistrarHitoDTO:
        cita = self.repositorio.obtener_cita_por_id(cita_id)
        if cita is None:
            return self._resultado(cita_id, hito, False, False, "cita_no_encontrada")

        campo = _campo_hito(hito)
        if cita.get(campo) is not None:
            return self._resultado(cita_id, hito, False, True, "hito_ya_registrado")

        valido, reason_code = _validar_orden_hito(hito, cita)
        if not valido:
            return self._resultado(cita_id, hito, False, False, reason_code)

        aplicado = self.repositorio.actualizar_hito_atencion(cita_id, campo, marca_tiempo or self.reloj.ahora())
        reason = "ok" if aplicado else "cita_no_encontrada"
        return self._resultado(cita_id, hito, aplicado, False, reason)

    def _resultado(
        self,
        cita_id: int,
        hito: HitoAtencion,
        aplicado: bool,
        ya_estaba: bool,
        reason_code: str,
    ) -> ResultadoRegistrarHitoDTO:
        LOGGER.info(
            "cita_registrar_hito",
            extra={
                "action": "cita_registrar_hito",
                "cita_id": cita_id,
                "hito": hito.value,
                "aplicado": aplicado,
                "reason_code": reason_code,
            },
        )
        return ResultadoRegistrarHitoDTO(aplicado=aplicado, ya_estaba=ya_estaba, reason_code=reason_code)


def _campo_hito(hito: HitoAtencion) -> str:
    campos = {
        HitoAtencion.CHECK_IN: "check_in_at",
        HitoAtencion.LLAMADO: "llamado_a_consulta_at",
        HitoAtencion.INICIO_CONSULTA: "consulta_inicio_at",
        HitoAtencion.FIN_CONSULTA: "consulta_fin_at",
        HitoAtencion.CHECK_OUT: "check_out_at",
    }
    return campos[hito]


def _validar_orden_hito(hito: HitoAtencion, cita: dict[str, object]) -> tuple[bool, str]:
    if hito is HitoAtencion.FIN_CONSULTA and cita.get("consulta_inicio_at") is None:
        return False, "orden_invalido_requiere_inicio_consulta"
    if hito is HitoAtencion.CHECK_OUT and cita.get("consulta_fin_at") is None:
        return False, "orden_invalido_requiere_fin_consulta"
    if hito is HitoAtencion.INICIO_CONSULTA and cita.get("check_in_at") is None:
        return True, "ok_sin_check_in"
    return True, "ok"
